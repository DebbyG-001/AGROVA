import { Button, Logo, Tag } from "@/components/ui";
import { HeroVideo } from "@/components/hero-video";
import { Reveal } from "@/components/reveal";

const loop = [
  { n: "01", t: "Talk", d: "Type or send a voice note in English or Pidgin — in the app or on WhatsApp." },
  { n: "02", t: "Record", d: "Agrova pulls out the purchase, sale, feed or health note and asks you to confirm." },
  { n: "03", t: "Understand", d: "Spending, profit and health risk are worked out from your real records." },
  { n: "04", t: "Act", d: "Reminders and early warnings tell you what needs attention before it costs you." },
];

const pidgin = [
  ["I don sell 20 birds.", "Sale · 20 birds"],
  ["Three don kpai.", "Mortality · 3 animals"],
  ["Dem no dey chop.", "Health observation · reduced feeding"],
  ["Abeg remind me tomorrow.", "Reminder · tomorrow"],
];

const features = [
  ["AI Farm Assistant", "Talk to your farm. Agrova turns what you say into structured records."],
  ["Multi-livestock", "Poultry, goats, sheep, cattle, pigs and rabbits in one place."],
  ["Profit Intelligence", "Revenue, costs and estimated profit — calculated, never guessed."],
  ["Health Assistant", "Describe symptoms or add a photo. Get a risk level and next steps."],
  ["Early Warning", "Spot rising mortality or unusual feed use before it becomes a loss."],
  ["Reminders", "Vaccination and medication tasks so nothing is missed."],
];

export default function Landing() {
  return (
    <main>
      <header className="sticky top-0 z-20 flex items-center justify-between bg-lime px-5 py-3 md:px-8">
        <Logo />
        <nav className="label hidden items-center gap-6 md:flex" aria-label="Main">
          <a href="#how">How it works</a>
          <a href="#language">Language</a>
          <a href="#features">Features</a>
        </nav>
        <Button href="/app" variant="forest" className="!min-h-9 !px-4">
          Start your farm
        </Button>
      </header>

      {/* Hero */}
      <section className="relative isolate grid min-h-[calc(100dvh-60px)] grid-cols-1 overflow-hidden bg-forest text-white md:grid-cols-2">
        <HeroVideo />
        <div className="relative flex flex-col justify-between gap-16 p-6 md:p-10">
          <h1 className="h-display text-[2.5rem] sm:text-5xl lg:text-6xl">
            Your farm
            <br />
            understands
            <br />
            you now
          </h1>
          <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
            <div className="max-w-sm">
              <p className="label mb-2 text-lime">
                <Tag>Meet Agrova,</Tag>
              </p>
              <p className="text-white/90">
                The AI farm companion built for African farmers. Agrova turns everyday farm
                conversations into records, insights, health guidance and early warnings.
              </p>
            </div>
            <div className="flex shrink-0 flex-col gap-3">
              <Button href="/app" className="!min-h-14 !px-9 !text-base whitespace-nowrap">
                Start your farm
              </Button>
              <Button href="#how" variant="outlineLight" className="!min-h-14 !px-9 !text-base whitespace-nowrap">
                See how it works
              </Button>
            </div>
          </div>
        </div>

        <div className="relative flex min-h-[32rem] flex-col justify-between gap-10 p-6 md:p-10">
          <div className="relative mx-auto w-full max-w-sm space-y-3 pt-4" aria-label="Example conversation">
            <Bubble who="you" delay={600}>I don buy 200 broiler yesterday for 300k.</Bubble>
            <Bubble who="agrova" delay={1600}>
              I understood: purchased <b>200 broilers</b> yesterday for <b>₦300,000</b>. Should I
              save this?
            </Bubble>
            <Bubble who="you" delay={2800}>Yes.</Bubble>
            <Bubble who="agrova" delay={3600}>Done. Added to your farm records.</Bubble>
          </div>
          <dl className="relative mx-auto grid w-full max-w-sm grid-cols-2 gap-6 text-sm">
            <div>
              <dt className="mb-2 font-mono text-lime">[01]</dt>
              <dd className="mb-1 font-bold">Voice + Pidgin</dd>
              <dd className="opacity-80">Speak the way you speak</dd>
            </div>
            <div>
              <dt className="mb-2 font-mono text-lime">[02]</dt>
              <dd className="mb-1 font-bold">App + WhatsApp</dd>
              <dd className="opacity-80">One farm database</dd>
            </div>
          </dl>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="px-5 py-20 md:px-10">
        <p className="label mb-3"><Tag>How it works</Tag></p>
        <h2 className="h-display mb-10 max-w-3xl text-3xl md:text-4xl">
          Talk. Record. Understand. Act.
        </h2>
        <ol className="grid gap-px overflow-hidden rounded-2xl bg-forest/15 md:grid-cols-4">
          {loop.map((s, i) => (
            <Reveal as="li" key={s.n} delay={i * 130} className="bg-paper p-6">
              <span className="font-mono text-leaf">[{s.n}]</span>
              <h3 className="mt-6 mb-2 text-xl font-bold">{s.t}</h3>
              <p className="text-forest/80">{s.d}</p>
            </Reveal>
          ))}
        </ol>
      </section>

      {/* Pidgin */}
      <section id="language" className="bg-forest px-5 py-20 text-white md:px-10">
        <p className="label mb-3 text-lime"><Tag>Built for how you talk</Tag></p>
        <h2 className="h-display mb-3 max-w-3xl text-3xl text-lime md:text-4xl">
          Not translated. Understood.
        </h2>
        <p className="mb-10 max-w-xl opacity-85">
          Agrova reads meaning and intent in Nigerian English and Pidgin, then turns it into a farm
          action. More African languages are on the roadmap.
        </p>
        <ul className="grid gap-3 md:grid-cols-2">
          {pidgin.map(([say, does], i) => (
            <Reveal as="li" key={say} delay={(i % 2) * 120} className="rounded-2xl border border-white/15 p-5">
              <p className="font-mono text-lg">“{say}”</p>
              <p className="label mt-3 text-lime">→ {does}</p>
            </Reveal>
          ))}
        </ul>
      </section>

      {/* Features */}
      <section id="features" className="px-5 py-20 md:px-10">
        <p className="label mb-3"><Tag>Features</Tag></p>
        <h2 className="h-display mb-10 max-w-3xl text-3xl md:text-4xl">
          One companion for the whole farm
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(([t, d], i) => (
            <Reveal as="li" key={t} delay={(i % 3) * 120} className="rounded-2xl border border-forest/10 bg-white p-6">
              <span className="font-mono text-leaf">[0{i + 1}]</span>
              <h3 className="mt-5 mb-2 text-lg font-bold">{t}</h3>
              <p className="text-forest/80">{d}</p>
            </Reveal>
          ))}
        </ul>
      </section>

      {/* CTA */}
      <section className="bg-lime px-5 py-20 text-center md:px-10">
        <h2 className="h-display mx-auto mb-6 max-w-2xl text-3xl md:text-4xl">
          Tell Agrova what happened on your farm today
        </h2>
        <Button href="/app" variant="forest">
          Start your farm
        </Button>
      </section>

      <footer className="flex flex-col gap-2 bg-forest px-5 py-8 text-sm text-lime md:flex-row md:justify-between md:px-10">
        <Logo light />
        <p className="opacity-80">
          Agrova provides AI-assisted decision support and does not replace professional veterinary
          diagnosis.
        </p>
      </footer>
    </main>
  );
}

function Bubble({
  who,
  delay = 0,
  children,
}: {
  who: "you" | "agrova";
  delay?: number;
  children: React.ReactNode;
}) {
  const mine = who === "you";
  return (
    <div className={`bubble-in flex ${mine ? "justify-end" : "justify-start"}`} style={{ animationDelay: `${delay}ms` }}>
      <p
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-[0.95rem] ${
          mine ? "bg-lime text-forest" : "bg-forest/70 text-white backdrop-blur-sm"
        }`}
      >
        {children}
      </p>
    </div>
  );
}
