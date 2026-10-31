import ThemeToggle from "./ThemeToggle";
import UserMenu from "./UserMenu";

export default function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-b-border border-t-2 border-t-red bg-bg/95 backdrop-blur lg:hidden">
      <div className="flex h-14 items-center gap-2 px-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo.png" alt="" width={32} height={32} className="size-8 rounded-md object-contain" />
        <span className="flex-1 font-display text-xl font-bold uppercase tracking-wide">
          MISTERY JUNGLE
        </span>
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
