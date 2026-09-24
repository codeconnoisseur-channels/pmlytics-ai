import { ChevronDown } from 'lucide-react';

const questions = [
  {
    question: 'How does PMLytics reach a recommendation?',
    answer: 'PMLytics investigates customer support, product analytics, and engineering context separately. It then compares the evidence and reviews the recommendation for unsupported claims before presenting it.',
  },
  {
    question: 'What if the available evidence is incomplete?',
    answer: 'PMLytics distinguishes supported findings from assumptions. When the data cannot support a responsible decision, the brief identifies what is missing and what your team should validate next.',
  },
  {
    question: 'Which systems can I connect?',
    answer: 'The current product brings together Zendesk, PostHog, and Jira through read-only integrations. Its integration layer can support additional systems without exposing raw infrastructure details in the report.',
  },
  {
    question: 'Does PMLytics make changes in connected tools?',
    answer: 'No. The current product is read-only. It investigates and recommends without creating issues, changing tickets, or modifying analytics configuration.',
  },
  {
    question: 'Who can access an investigation?',
    answer: 'Live investigations are private to the account that created them. Public sample briefs are available for evaluation without signing in.',
  },
];

export function FAQSection() {
  return (
    <section id="faq" className="scroll-mt-24 border-b border-black/10 bg-[#fbfcf9] py-20 sm:py-28">
      <div className="mx-auto grid max-w-[1100px] gap-10 px-5 sm:px-8 lg:grid-cols-[0.7fr_1.3fr] lg:gap-16">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.16em] text-[#6c7168]">FAQ</p>
          <h2 className="mt-4 text-balance text-3xl font-black leading-[1.05] tracking-[-0.045em] text-[#171915] sm:text-5xl">
            What to know before your first investigation.
          </h2>
          <p className="mt-5 max-w-md text-pretty text-base leading-7 text-[#62675f]">
            Clear answers about connected data, uncertainty, access, and the limits of the product today.
          </p>
        </div>

        <div className="divide-y divide-black/10 border-y border-black/10">
          {questions.map((item) => (
            <details key={item.question} className="group py-1">
              <summary className="flex min-h-16 cursor-pointer touch-manipulation list-none items-center justify-between gap-4 rounded-lg px-2 py-4 text-left text-base font-bold text-[#171915] hover:bg-[#f4f5f2] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#171915] [&::-webkit-details-marker]:hidden">
                {item.question}
                <ChevronDown className="h-5 w-5 shrink-0 text-[#777c74] transition-transform group-open:rotate-180 motion-reduce:transition-none" aria-hidden="true" />
              </summary>
              <p className="px-2 pb-5 pr-10 text-sm leading-7 text-[#62675f]">{item.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
