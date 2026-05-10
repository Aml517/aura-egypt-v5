// frontend/pages/_app.jsx
import '../styles/globals.css'
import Head from 'next/head'

export default function App({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>AuraEgypt — Cinematic Travel Discovery</title>
        <meta name="description" content="Match a film's emotional soul to an Egyptian destination. AI-powered travel for the discerning explorer." />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <meta property="og:title" content="AuraEgypt" />
        <meta property="og:description" content="Find your cinematic portal to Egypt" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>𓂀</text></svg>" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}