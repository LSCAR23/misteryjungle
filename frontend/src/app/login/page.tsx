import type { Metadata } from "next";
import LoginForm from "./LoginForm";

export const metadata: Metadata = { title: "Entrar · Mistery Jungle" };

export default function LoginPage() {
  return (
    <main className="relative flex min-h-dvh flex-1 items-center justify-center overflow-hidden px-4 py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 left-1/2 h-48 w-[140%] -translate-x-1/2 -skew-y-6 bg-red opacity-90"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-10 left-1/2 h-4 w-[140%] -translate-x-1/2 -skew-y-6 bg-bg"
      />
      <LoginForm />
    </main>
  );
}
