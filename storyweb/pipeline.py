import spacy
import logging
from spacy.tokens import Span
from pathlib import Path
from typing import Generator, List, Optional, Tuple
from functools import cache
from normality import slugify
from articledata import Article
from pydantic import ValidationError

from storyweb.db import engine
from storyweb.clean import clean_entity_name
from storyweb.models import Ref, Sentence, Tag

log = logging.getLogger(__name__)


@cache
def load_nlp():
    # spacy.prefer_gpu()
    # disable everything but NER:
    nlp = spacy.load(
        "en_core_web_trf",
        # "en_core_web_sm",
        disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"],
    )
    nlp.add_pipe("sentencizer")
    return nlp


def read_articles(path: Path) -> Generator[Tuple[str, Article], None, None]:
    with open(path, "rb") as fh:
        while line := fh.readline():
            try:
                article = Article.parse_raw(line)
                if article.id is None:
                    continue
                if article.language != "eng":
                    continue
                yield (article.text, article)
            except ValidationError as ve:
                log.warn("Article validation [%s]: %s", article.id, ve)


def make_tag(ref_id: str, seq: int, ent: Span) -> Optional[Tag]:
    category = ent.label_
    if category not in ["PERSON", "ORG", "GPE"]:
        return None
    text = clean_entity_name(ent.text)
    fp = slugify(text, sep="-")
    if fp is None:
        return None
    fp = "-".join(sorted(fp.split("-")))
    if category == "PERSON" and " " not in text:
        return None
    key = f"{category.lower()}:{fp}"
    return Tag(
        ref_id=ref_id,
        sentence=seq,
        key=key,
        category=category,
        text=text,
    )


def load_articles(path: Path) -> None:
    nlp = load_nlp()
    articles = read_articles(path)
    for (doc, article) in nlp.pipe(articles, batch_size=20, as_tuples=True):
        print(article.language, article.id)
        ref = Ref(
            id=article.id,
            site=article.site,
            url=article.url,
            title=article.title,
        )

        sentences: List[Sentence] = []
        tags: List[Tag] = []
        for seq, sent in enumerate(doc.sents):
            sent_tags = 0
            for ent in sent.ents:
                tag = make_tag(ref.id, seq, ent)
                if tag is not None:
                    tags.append(tag)
                    sent_tags += 1

            if sent_tags > 0:
                sentence = Sentence(ref_id=ref.id, sequence=seq, text=sent.text)
                sentences.append(sentence)

        with engine.begin() as conn:
            ref.save(conn)
            Sentence.clear_ref(conn, ref.id)
            Tag.clear_ref(conn, ref.id)
            Sentence.save_many(conn, sentences)
            Tag.save_many(conn, tags)
