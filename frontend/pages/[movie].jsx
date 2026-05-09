import { useRouter } from 'next/router'

export default function MoviePage() {
  const router = useRouter();
  const { movie } = router.query;

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-10">
      <h1 className="text-5xl font-bold text-yellow-500 mb-4 uppercase tracking-widest text-center">
        The {movie} Portal
      </h1>
      <p className="text-xl italic text-white/60 text-center max-w-2xl">
        Cleopatra is preparing a cinematic journey for those who seek the vibe of "{movie}"...
      </p>
      <button 
        onClick={() => window.location.href = '/'}
        className="mt-10 px-8 py-3 border border-yellow-700 text-yellow-700 hover:bg-yellow-700 hover:text-black transition-all rounded-full"
      >
        Return to the Oracle
      </button>
    </div>
  )
}