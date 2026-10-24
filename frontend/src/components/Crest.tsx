// Original Campus Customs crest (not the Yale shield): a navy shield, gold rules, CC monogram, 1975.
export default function Crest({ size = 44, className = "" }: { size?: number; className?: string }) {
  return (
    <svg className={`crest-mark ${className}`} width={size} height={size * 1.15} viewBox="0 0 100 115" aria-hidden="true">
      <defs>
        <linearGradient id="crest-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f3dfa6" />
          <stop offset=".5" stopColor="#c9a45c" />
          <stop offset="1" stopColor="#9c7a3c" />
        </linearGradient>
        <linearGradient id="crest-navy" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0d3a74" />
          <stop offset="1" stopColor="#00214a" />
        </linearGradient>
      </defs>
      <path d="M50 3 L95 14 V55 C95 84 74 101 50 112 C26 101 5 84 5 55 V14 Z" fill="url(#crest-navy)" stroke="url(#crest-gold)" strokeWidth="3.5" />
      <path d="M50 11 L87 20 V55 C87 79 70 93 50 103 C30 93 13 79 13 55 V20 Z" fill="none" stroke="url(#crest-gold)" strokeWidth="1" opacity=".8" />
      <text x="50" y="66" textAnchor="middle" fontFamily="'Cormorant Garamond', Georgia, serif" fontSize="40" fontWeight="700" fill="url(#crest-gold)" letterSpacing="-1">CC</text>
      <path d="M28 76 H72" stroke="url(#crest-gold)" strokeWidth="1" />
      <text x="50" y="90" textAnchor="middle" fontFamily="Georgia, serif" fontSize="11" letterSpacing="3" fill="#f3dfa6">1975</text>
      <path d="M50 22 l3 6 6 .8-4.5 4.2 1.1 6.2-5.6-3-5.6 3 1.1-6.2-4.5-4.2 6-.8z" fill="url(#crest-gold)" transform="translate(0 -2) scale(1)" />
    </svg>
  );
}
