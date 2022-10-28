import type { GetServerSidePropsContext } from 'next'
import Link from 'next/link';

import Layout from '../../components/Layout'
import { ITag, IListingResponse, ICluster, IClusterDetails, IRelatedCluster, ISimilarCluster, IArticle, IArticleDetails } from '../../lib/types';

import { getClusterLink, getLinkLoomLink } from '../../lib/util';
import { SpacedList, Spacer, TagCategory, TagLabel } from '../../components/util';
import { fetchJson } from '../../lib/data';
import { HTMLTable, Tab, Tabs } from '@blueprintjs/core';
import SimilarListing from '../../components/SimilarListing';
import RelatedListing from '../../components/RelatedListing';
import ArticleText from '../../components/ArticleText';

interface ArticleViewProps {
  article: IArticleDetails
}

export default function ArticleView({ article }: ArticleViewProps) {
  return (
    <Layout title={article.title}>
      <h1>
        {article.title}
      </h1>
      <p>
        Site: {article.site} <Spacer />
        <a href={article.url}>{article.url}</a>
      </p>
      <ArticleText text={article.text} tags={[['and', 'or'], ['if', 'when']]} />
    </Layout>
  )
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  const articleId = context.params?.id as string;
  const article = await fetchJson<IArticleDetails>(`/articles/${articleId}`);

  // const clusters = `/clusters/${cluster.id}/similar`;
  // const similar = await fetchJson<IListingResponse<ICluster>>(similarPath);
  return {
    props: { article },
  }
}
