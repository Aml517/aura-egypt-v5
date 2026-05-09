import Head from 'next/head';
import '../styles/globals.css';

function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>AuraEgypt | Your Movie's Egypt Trip</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="AI plans your cinematic Egypt adventure." />
      </Head>

      <main className="min-h-screen bg-black text-white font-sans selection:bg-yellow-500 selection:text-black">
        <Component {...pageProps} />
      </main>

      <style jsx global>{`
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #854d0e; border-radius: 10px; }
      `}</style>
    </>
  );
}

export default MyApp;