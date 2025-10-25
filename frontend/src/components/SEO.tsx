import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';

/**
 * SEO Component with Open Graph, Twitter Cards, and Schema.org
 */

interface SEOProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  type?: 'website' | 'article' | 'product';
  author?: string;
  publishedTime?: string;
  modifiedTime?: string;
  tags?: string[];
  noindex?: boolean;
}

export const SEO: React.FC<SEOProps> = ({
  title,
  description,
  image = '/og-image.png',
  url,
  type = 'website',
  author,
  publishedTime,
  modifiedTime,
  tags = [],
  noindex = false,
}) => {
  const { t, i18n } = useTranslation();
  
  // Default values
  const defaultTitle = t('seo.title', 'Blockchain Forensics - AI-Powered Crypto Investigation Platform');
  const defaultDescription = t('seo.description', 
    'Enterprise blockchain forensics and AML compliance platform. Trace crypto transactions, detect fraud, and ensure regulatory compliance across 35+ blockchains.'
  );
  
  const siteUrl = process.env.VITE_SITE_URL || 'https://blockchain-forensics.com';
  const fullUrl = url ? `${siteUrl}${url}` : siteUrl;
  const fullTitle = title ? `${title} | Blockchain Forensics` : defaultTitle;
  const fullDescription = description || defaultDescription;
  const fullImage = image.startsWith('http') ? image : `${siteUrl}${image}`;
  
  // Schema.org structured data
  const schemaOrg = {
    '@context': 'https://schema.org',
    '@type': type === 'article' ? 'Article' : 'WebApplication',
    name: fullTitle,
    description: fullDescription,
    url: fullUrl,
    image: fullImage,
    applicationCategory: 'SecurityApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'AggregateOffer',
      priceCurrency: 'USD',
      lowPrice: '0',
      highPrice: '50000',
    },
    provider: {
      '@type': 'Organization',
      name: 'Blockchain Forensics',
      url: siteUrl,
      logo: `${siteUrl}/logo.png`,
    },
    ...(author && { author: { '@type': 'Person', name: author } }),
    ...(publishedTime && { datePublished: publishedTime }),
    ...(modifiedTime && { dateModified: modifiedTime }),
    ...(tags.length > 0 && { keywords: tags.join(', ') }),
  };
  
  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <html lang={i18n.language} />
      <title>{fullTitle}</title>
      <meta name="description" content={fullDescription} />
      <link rel="canonical" href={fullUrl} />
      
      {/* Robots */}
      {noindex && <meta name="robots" content="noindex,nofollow" />}
      
      {/* Open Graph (Facebook, LinkedIn) */}
      <meta property="og:type" content={type} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={fullDescription} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:image" content={fullImage} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:site_name" content="Blockchain Forensics" />
      <meta property="og:locale" content={i18n.language} />
      
      {/* Twitter Cards */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={fullDescription} />
      <meta name="twitter:image" content={fullImage} />
      <meta name="twitter:site" content="@BlockchainForensics" />
      <meta name="twitter:creator" content="@BlockchainForensics" />
      
      {/* Article Meta (if type is article) */}
      {type === 'article' && publishedTime && (
        <meta property="article:published_time" content={publishedTime} />
      )}
      {type === 'article' && modifiedTime && (
        <meta property="article:modified_time" content={modifiedTime} />
      )}
      {type === 'article' && author && (
        <meta property="article:author" content={author} />
      )}
      {type === 'article' && tags.map(tag => (
        <meta key={tag} property="article:tag" content={tag} />
      ))}
      
      {/* Schema.org Structured Data */}
      <script type="application/ld+json">
        {JSON.stringify(schemaOrg)}
      </script>
      
      {/* Additional SEO Tags */}
      <meta name="theme-color" content="#6366f1" />
      <meta name="msapplication-TileColor" content="#6366f1" />
      
      {/* Mobile */}
      <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
      <meta name="format-detection" content="telephone=no" />
      
      {/* Security */}
      <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    </Helmet>
  );
};

export default SEO;
