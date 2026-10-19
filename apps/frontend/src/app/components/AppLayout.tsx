import type { ReactNode } from "react";
import { Link } from "react-router";
import { useSession } from "../../features/auth/session/SessionProvider";
import { AccountMenu } from "../../features/auth/components/AccountMenu";

export function AppLayout({ children }: { children: ReactNode }) {
  const { state } = useSession();
  return (
    <>
      <a className="fixed -top-25 left-4 z-10 bg-white p-4 focus:top-4" href="#main">
        Skip to content
      </a>
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex min-h-21.25 max-w-300 items-center gap-[1.3rem] px-8 py-[1.1rem] max-compact:flex-wrap max-compact:gap-[0.8rem] max-compact:p-4">
          <Link
            className="flex items-center gap-[0.65rem] font-brand text-[1.4rem] font-bold whitespace-nowrap text-ink no-underline"
            to="/sites"
          >
            <span
              className="size-6 rounded-[50%] bg-solar shadow-[inset_-6px_-3px_0_var(--color-solar-shade)]"
              aria-hidden="true"
            />
            Solar sites
          </Link>
          <span className="border-l border-line pl-[1.3rem] text-[0.9rem] text-muted max-wide:hidden">
            Advisor workspace
          </span>
          {state.status === "authenticated" ? <AccountMenu email={state.email} /> : null}
        </div>
      </header>
      {children}
      <footer className="px-8 py-6 text-center text-[0.8rem] text-muted">
        Solar estimates for informed client conversations.
      </footer>
    </>
  );
}
