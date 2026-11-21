export function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden>
      <rect width="40" height="40" rx="11" fill="#141412" />
      {/* rack slots */}
      <rect x="10" y="20" width="20" height="3" rx="1.5" fill="#f6f3ec" opacity="0.9" />
      <rect x="10" y="25.5" width="20" height="3" rx="1.5" fill="#f6f3ec" opacity="0.65" />
      <rect x="10" y="31" width="20" height="3" rx="1.5" fill="#f6f3ec" opacity="0.4" />
      {/* rising heat */}
      <path d="M13 15c2-2.6 4-2.6 6 0s4 2.6 6 0 2.6-2.4 3.5-1.4" stroke="#f2a65a" strokeWidth="2.6" fill="none" strokeLinecap="round" />
      <path d="M13 9.5c2-2.6 4-2.6 6 0s4 2.6 6 0" stroke="#c0653a" strokeWidth="2.2" fill="none" strokeLinecap="round" opacity="0.8" />
    </svg>
  );
}

export function Logo() {
  return (
    <div className="flex items-center gap-2.5">
      <LogoMark />
      <div className="leading-none">
        <div className="font-display text-[21px] font-semibold">DigitalHeat</div>
        <div className="mt-1 text-[10.5px] uppercase tracking-[0.14em] text-rust">Fleet console</div>
      </div>
    </div>
  );
}
