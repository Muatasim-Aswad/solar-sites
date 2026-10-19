import { Link, Navigate } from "react-router";
import { useSession } from "./session/SessionProvider";
import { CredentialsForm } from "./components/CredentialsForm";
import { Notice } from "../../shared/ui/feedback";
import { Panel } from "../../shared/ui/layout";

export function AuthPage({ mode }: { mode: "login" | "register" }) {
  const { state } = useSession();
  if (state.status === "authenticated") return <Navigate to="/sites" replace />;
  const registering = mode === "register";
  const title = registering ? "Create an advisor account" : "Welcome back";
  return (
    <main
      id="main"
      className="mx-auto grid min-h-[calc(100vh-160px)] max-w-275 grid-cols-2 items-center gap-20 px-8 py-20 max-wide:gap-8 max-wide:pt-12 max-compact:block max-compact:px-4 max-compact:py-8"
    >
      <section className="max-compact:mb-8">
        <div
          className="mb-8 grid w-fit -skew-y-10 grid-cols-[repeat(2,20px)] gap-1 max-compact:hidden"
          aria-hidden="true"
        >
          <span className="size-5 rounded-xs bg-teal" />
          <span className="size-5 rounded-xs bg-teal" />
          <span className="size-5 rounded-xs bg-teal" />
          <span className="size-5 rounded-xs bg-solar" />
        </div>
        <h1 className="max-w-[15ch] text-[clamp(2.2rem,4vw,3.2rem)] max-compact:max-w-[22ch] max-compact:text-[2rem]">
          Put a roof’s potential into perspective.
        </h1>
        <p className="mt-[1.2rem] max-w-[42ch] max-compact:mt-[0.8rem]">
          Estimate solar production and show clients how a battery changes the energy they use at
          home.
        </p>
        <p className="mt-[1.2rem] max-w-[42ch] text-muted max-compact:mt-[0.8rem]">
          Your client sites stay private to your account.
        </p>
      </section>
      <Panel padding="auth" aria-labelledby="auth-title">
        <h2 id="auth-title">{title}</h2>
        {state.status === "anonymous" && state.expired ? (
          <Notice as="output">Your session has ended. Log in to continue.</Notice>
        ) : null}
        <CredentialsForm mode={mode} />
        <p className="mt-[1.6rem] mb-0 text-[0.9rem]">
          {registering ? "Already have an account? " : "New advisor? "}
          <Link to={registering ? "/login" : "/register"}>
            {registering ? "Log in" : "Create an account"}
          </Link>
        </p>
      </Panel>
    </main>
  );
}
