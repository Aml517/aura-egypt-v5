/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        gold:      '#D4AF37',
        'gold-lt': '#E8CC6A',
        'gold-dk': '#A8861A',
        royal:     '#002366',
        'royal-md':'#0A3080',
        'royal-lt':'#1A4DB3',
        sand:      '#F5F1E4',
        parchment: '#FBF8F0',
        stone:     '#8B7D6B',
        'stone-lt':'#B8A99A',
        ink:       '#0D0A06',
        community: '#1A5C3A',
        terr:      '#8B3A2A',
      },
      fontFamily: {
        display: ['"Cinzel"', 'Georgia', 'serif'],
        serif:   ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans:    ['"DM Sans"', 'system-ui', 'sans-serif'],
      },
      animation: {
        'shimmer':      'shimmer 4s linear infinite',
        'lotus-out':    'lotus-out 3s linear infinite',
        'lotus-in':     'lotus-in 2s linear infinite',
        'dot-pulse':    'dot-pulse 1.4s ease-in-out infinite',
        'bar-fill':     'bar-fill 1.4s cubic-bezier(0.4,0,0.2,1) 0.3s both',
        'fade-up':      'fade-up 0.6s cubic-bezier(0.4,0,0.2,1) both',
        'scan':         'scan 2s ease-in-out infinite',
      },
      keyframes: {
        shimmer: {
          '0%':   { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition:  '200% center' },
        },
        'lotus-out': {
          '0%':   { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'lotus-in': {
          '0%':   { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(-360deg)' },
        },
        'dot-pulse': {
          '0%,80%,100%': { transform: 'scale(0.6)', opacity: '0.4' },
          '40%':          { transform: 'scale(1.0)', opacity: '1'   },
        },
        'bar-fill': {
          from: { width: '0%' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(18px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        scan: {
          '0%,100%': { opacity: '0.3', transform: 'scaleX(0.6)' },
          '50%':     { opacity: '1',   transform: 'scaleX(1)' },
        },
      },
      boxShadow: {
        gold:    '0 0 24px rgba(212,175,55,0.35)',
        'gold-sm':'0 0 10px rgba(212,175,55,0.2)',
        royal:   '0 8px 32px rgba(0,35,102,0.15)',
        card:    '0 2px 16px rgba(13,10,6,0.08)',
      },
      backgroundImage: {
        'gold-gradient':   'linear-gradient(135deg, #D4AF37 0%, #E8CC6A 50%, #D4AF37 100%)',
        'royal-gradient':  'linear-gradient(135deg, #002366 0%, #0A3080 100%)',
        'parchment-grain': 'url("/grain.svg")',
      },
    },
  },
  plugins: [],
}