# C004: results. S0 FAILED; the sweep did not happen as registered

Run on the S25 by the operator on 2026-09-27 against the 37 frozen models, seed 1.

## Outcome by model

- **Ran: 1.** `google/gemma-4-31b-it`: baseline accuracy 0.9000, companion 0.9000, token gain 13.50,
  baseline lookup accuracy 1.0000.
- **Did not qualify: 8.** They failed the probe:
  - `deepseek-ai/deepseek-v4.1-flash`, `moonshotai/kimi-k3`, `openai/gpt-oss-20b`, `z-ai/glm-5.3` and
    `z-ai/glm-5.3-flash` returned empty answers (reasoning models whose 16 tokens went on hidden
    reasoning);
  - `nvidia/nemotron-3-super-120b-a12b`, `nvidia/nemotron-3-ultra-550b-a55b` and
    `nvidia/nemotron-3.5-lightning-30b-a3b` began their answers by thinking out loud ("We need to
    answer…", "The user is asking…", "Here's a thinking process:").
- **Could not run: 28.** 26 returned **HTTP 404 Not Found**, although all 26 appear in the key's
  `/models` listing. `mistralai/mistral-nemotron` timed out partway through its run, and
  `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` returned HTTP 503 partway through.

The runner's summary line: `qualified and ran: 1 of 37; gain min 13.50; companion within one question
of baseline on 1/1; median accuracy difference +0.0000`.

## Verdicts

| | registered | measured | |
|---|---|---|---|
| S0 | at least 10 models qualify and complete | 1 | **FAILED** |
| S1-S3 | over the qualifying models | 1 model: gain 13.50, within tolerance, difference +0.0000 | not assessable: one model is not a sweep |

## What this shows

- **The key's model list is not the list of models the key can use.** 26 listed models answered 404.
  I registered the sweep from the listing without first checking which models actually serve. That
  is the same mistake as E004 (a threshold nobody had checked), in a different place. It is kept here.
- **Reasoning models do not fit a 16-token answer format.** That is a property of the test harness,
  not of the companion. A sweep that includes them needs a larger answer budget, or a way to read
  their final answer, registered in advance.
- The one model that ran (Gemma 4 31B) matched C001's behaviour: 13.50× fewer tokens at equal
  accuracy.

## Next (C004b, to be registered only after a serving check)

1. Run a serving-only probe over the listing (one tiny request per model; no scoring) and freeze the
   list of models that actually answer.
2. Decide in advance how reasoning models are handled.
3. Then register and run.
