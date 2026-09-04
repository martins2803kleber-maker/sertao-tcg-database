/* tslint:disable */
/* eslint-disable */

export function add_card(duel_id: number, team: number, code: number, location: number): void;

export function bridge_version(): string;

export function clear_registered_cards(): void;

export function clear_registered_scripts(): void;

export function create_duel(extra_flags: number): number;

export function destroy_duel(duel_id: number): void;

export function init_engine(): Promise<any>;

export function load_script(duel_id: number, name: string, source: string): boolean;

export function process_duel(duel_id: number): any;

export function register_cards(json: string): number;

export function register_scripts(json: string): number;

export function set_response_bytes(duel_id: number, bytes: Uint8Array): void;

export function set_response_i(duel_id: number, value: number): void;

export function start_duel(duel_id: number): void;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly add_card: (a: number, b: number, c: number, d: number) => [number, number];
    readonly bridge_version: () => [number, number];
    readonly clear_registered_cards: () => void;
    readonly clear_registered_scripts: () => void;
    readonly create_duel: (a: number) => [number, number, number];
    readonly destroy_duel: (a: number) => [number, number];
    readonly init_engine: () => any;
    readonly load_script: (a: number, b: number, c: number, d: number, e: number) => [number, number, number];
    readonly process_duel: (a: number) => [number, number, number];
    readonly register_cards: (a: number, b: number) => [number, number, number];
    readonly register_scripts: (a: number, b: number) => [number, number, number];
    readonly set_response_bytes: (a: number, b: any) => [number, number];
    readonly set_response_i: (a: number, b: number) => [number, number];
    readonly start_duel: (a: number) => [number, number];
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__u32__i32__true_: (a: number, b: number, c: number, d: number, e: number) => number;
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true_: (a: number, b: number, c: number, d: number, e: number) => void;
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true__2: (a: number, b: number, c: number, d: number, e: number) => void;
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue__core_ed718c3d60ebd546___result__Result_____wasm_bindgen_d1a1f5b9c1e1d7e3___JsError___true_: (a: number, b: number, c: any) => [number, number];
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32______true_: (a: number, b: number, c: number, d: number) => void;
    readonly wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined_______true_: (a: number, b: number, c: any, d: any) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_destroy_closure: (a: number, b: number) => void;
    readonly __externref_table_dealloc: (a: number) => void;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
