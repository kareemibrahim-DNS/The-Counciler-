import { defineEval } from "@grok/agent-sdk/evals";

export default defineEval({
  tags: ["smoke"],
  description: "Reseller questions hit catalog tools; off-topic is refused.",
  cases: [
    {
      id: "partners-by-country",
      description: "Lists partners for Saudi Arabia via list_partners.",
      async test(t) {
        await t.send(
          "What partners are available for the reseller program in Saudi Arabia (SA)?",
        );
        t.succeeded();
        t.calledTool("list_partners");
        t.notCalledTool("get_line_item_price");
      },
    },
    {
      id: "price-requires-country",
      description:
        "Looks up Ballurh Subscription Base price in SA via get_line_item_price.",
      async test(t) {
        await t.send(
          "What is the price of Ballurh Subscription Base in Saudi Arabia (SA)?",
        );
        t.succeeded();
        t.calledTool("get_line_item_price");
      },
    },
    {
      id: "off-topic-refuse",
      description: "Off-topic questions do not call catalog tools.",
      async test(t) {
        await t.send("Write me a poem about coffee.");
        t.succeeded();
        t.notCalledTool("list_partners");
        t.notCalledTool("list_line_items");
        t.notCalledTool("get_quote_structure");
        t.notCalledTool("get_line_item_price");
      },
    },
  ],
});
