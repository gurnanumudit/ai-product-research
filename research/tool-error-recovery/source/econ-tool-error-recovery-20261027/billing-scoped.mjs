// Scoped IDEA19 copy of usage/money/generationId/reconcile; historical source unchanged.
// Source SHA256: e70b7f209dee8d778db532e16438a74ce2e44d1c68deebbfd47cd07c6cc59932
export const CONFIG = Object.freeze({model:'openai/gpt-6-luna', input_reservation_tokens:124096, max_output_tokens:8192});
const integer = x => Number.isSafeInteger(x) && x >= 0;
const check = (ok, code) => { if (!ok) throw new Error(code); };
const clone = x => JSON.parse(JSON.stringify(x));

export function usage(response) {
  const u = response.usage;
  check(u && typeof u === 'object', 'missing_usage');
  const v = { input: u.input_tokens, output: u.output_tokens, total: u.total_tokens,
    cached: u.input_tokens_details?.cached_tokens, reasoning: u.output_tokens_details?.reasoning_tokens };
  check(Object.values(v).every(integer), 'malformed_or_partial_usage');
  check(v.total === v.input + v.output && v.cached <= v.input && v.reasoning <= v.output,
    'inconsistent_usage');
  check(v.input <= CONFIG.input_reservation_tokens && v.output <= CONFIG.max_output_tokens,
    'usage_exceeds_reservation');
  const details = u.input_tokens_details;
  v.cache_write = Object.hasOwn(details, 'cache_write_tokens') ? details.cache_write_tokens : null;
  check(!Object.hasOwn(details, 'cache_write_tokens') || integer(v.cache_write), 'malformed_cache_write_usage');
  check(v.cache_write === null || v.cached + v.cache_write <= v.input, 'inconsistent_cache_usage');
  return v;
}

// Decimal money is rounded upward to nano-USD, never missing -> zero.
export function money(value) {
  check((typeof value === 'number' || typeof value === 'string') &&
    /^\d+(\.\d+)?$/.test(String(value)), 'unknown_charge');
  const [whole, fraction = ''] = String(value).split('.');
  const nanos = BigInt(whole) * 1000000000n + BigInt((fraction + '000000000').slice(0, 9))
    + (/[1-9]/.test(fraction.slice(9)) ? 1n : 0n);
  check(nanos <= BigInt(Number.MAX_SAFE_INTEGER), 'invalid_charge');
  return Number(nanos);
}
export function generationId(response) {
  const snake = response.provider_metadata?.gateway?.generationId;
  const camel = response.providerMetadata?.gateway?.generationId;
  check(!snake || !camel || snake === camel, 'generation_id_conflict');
  const metadataId = snake ?? camel;
  const id = metadataId ?? response.id;
  check(typeof id === 'string' && /^gen_[A-Za-z0-9_-]+$/.test(id), 'unknown_generation_id');
  if (metadataId && response.id?.startsWith('gen_')) check(metadataId === response.id, 'generation_id_conflict');
  return id;
}
export function reconcile(response, receipt, id) {
  const d = receipt?.data;
  check(d && d.id === id, 'receipt_id_mismatch');
  const cost = money(d.total_cost);
  check(d.gateway_cost == null || money(d.gateway_cost) === cost, 'charge_mismatch');
  check(d.surcharge_cost == null || money(d.surcharge_cost) <= cost, 'charge_mismatch');
  check(d.is_byok === false && (d.upstream_inference_cost == null || money(d.upstream_inference_cost) === 0), 'unbounded_byok_charge');
  check(d.provider_name === 'openai' && d.model === CONFIG.model, 'receipt_route_mismatch');
  check([CONFIG.model, 'gpt-6-luna'].includes(response.model), 'response_model_mismatch');
  const u = usage(response);
  check(integer(d.tokens_prompt) && integer(d.tokens_completion), 'partial_receipt_usage');
  for (const key of ['native_tokens_prompt', 'native_tokens_completion',
    'native_tokens_reasoning', 'native_tokens_cached', 'native_tokens_cache_creation',
    'billable_web_search_calls']) check(d[key] == null || integer(d[key]), 'malformed_receipt_usage');
  const completionIncludesReasoning = d.tokens_completion === u.output;
  const completionExcludesReasoning = integer(d.native_tokens_reasoning) &&
    d.native_tokens_reasoning === u.reasoning && d.tokens_completion + d.native_tokens_reasoning === u.output;
  const promptIncludesCache = d.tokens_prompt === u.input;
  const promptExcludesCache = integer(d.native_tokens_cached) && integer(d.native_tokens_cache_creation)
    && d.tokens_prompt + d.native_tokens_cached + d.native_tokens_cache_creation === u.input;
  // The exclusive convention requires BOTH explicit counts, including explicit zeros.
  // A response cache-write count, when present, must have matching receipt evidence.
  check((d.native_tokens_cached == null || d.native_tokens_cached <= u.input) &&
    (d.native_tokens_cache_creation == null || u.cached + d.native_tokens_cache_creation <= u.input) &&
    (!(integer(d.native_tokens_cached) && integer(d.native_tokens_cache_creation)) ||
      d.native_tokens_cached + d.native_tokens_cache_creation <= u.input) &&
    (u.cache_write === null || d.native_tokens_cache_creation === u.cache_write),
    'receipt_cache_usage_mismatch');
  check((promptIncludesCache || promptExcludesCache) && (completionIncludesReasoning || completionExcludesReasoning) &&
    (d.native_tokens_reasoning == null || d.native_tokens_reasoning === u.reasoning) &&
    (d.native_tokens_cached == null || d.native_tokens_cached === u.cached) &&
    (d.native_tokens_cache_creation == null || d.native_tokens_cache_creation <= u.input) &&
    (d.billable_web_search_calls == null || d.billable_web_search_calls === 0),
    'receipt_usage_mismatch');
  // Native provider token categories are preserved, not assumed interchangeable
  // with the normalized prompt/completion totals (see prior-study billing lessons).
  return { cost_nano_usd: cost, provider: d.provider_name, model: d.model, response_model: response.model,
    usage: u, receipt_prompt_convention: promptIncludesCache ? 'includes_cached_tokens' : 'excludes_separately_reported_cache_read_and_write',
    receipt_prompt_tokens: d.tokens_prompt,
    raw_response_usage: clone(response.usage), raw_receipt_data: clone(d),
    receipt_completion_convention: completionIncludesReasoning ? 'includes_reasoning' : 'excludes_separately_reported_reasoning', receipt_completion_tokens: d.tokens_completion, cache_write_tokens: d.native_tokens_cache_creation ?? null,
    optional_receipt_fields: Object.fromEntries(['gateway_cost', 'surcharge_cost', 'upstream_inference_cost', 'native_tokens_prompt', 'native_tokens_completion', 'native_tokens_reasoning', 'native_tokens_cached', 'native_tokens_cache_creation', 'billable_web_search_calls'].map(k=>[k,d[k] ?? null])),
    provenance: { endpoint: 'https://ai-gateway.vercel.sh/v1/generation', generation_id: id,
      cost_field: 'data.total_cost', usage_fields: 'response.usage + receipt.data.tokens_*' } };
}

