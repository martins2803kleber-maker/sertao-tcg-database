/* @ts-self-types="./duellab_engine.d.ts" */
import * as import1 from "./snippets/ocgcore-ffi-c6e3cc3310618123/ocgcore.js"


/**
 * @param {number} duel_id
 * @param {number} team
 * @param {number} code
 * @param {number} location
 */
export function add_card(duel_id, team, code, location) {
    const ret = wasm.add_card(duel_id, team, code, location);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}

/**
 * @returns {string}
 */
export function bridge_version() {
    let deferred1_0;
    let deferred1_1;
    try {
        const ret = wasm.bridge_version();
        deferred1_0 = ret[0];
        deferred1_1 = ret[1];
        return getStringFromWasm0(ret[0], ret[1]);
    } finally {
        wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
    }
}

export function clear_registered_cards() {
    wasm.clear_registered_cards();
}

export function clear_registered_scripts() {
    wasm.clear_registered_scripts();
}

/**
 * @param {number} extra_flags
 * @returns {number}
 */
export function create_duel(extra_flags) {
    const ret = wasm.create_duel(extra_flags);
    if (ret[2]) {
        throw takeFromExternrefTable0(ret[1]);
    }
    return ret[0] >>> 0;
}

/**
 * @param {number} duel_id
 */
export function destroy_duel(duel_id) {
    const ret = wasm.destroy_duel(duel_id);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}

/**
 * @returns {Promise<any>}
 */
export function init_engine() {
    const ret = wasm.init_engine();
    return ret;
}

/**
 * @param {number} duel_id
 * @param {string} name
 * @param {string} source
 * @returns {boolean}
 */
export function load_script(duel_id, name, source) {
    const ptr0 = passStringToWasm0(name, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len0 = WASM_VECTOR_LEN;
    const ptr1 = passStringToWasm0(source, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len1 = WASM_VECTOR_LEN;
    const ret = wasm.load_script(duel_id, ptr0, len0, ptr1, len1);
    if (ret[2]) {
        throw takeFromExternrefTable0(ret[1]);
    }
    return ret[0] !== 0;
}

/**
 * @param {number} duel_id
 * @returns {any}
 */
export function process_duel(duel_id) {
    const ret = wasm.process_duel(duel_id);
    if (ret[2]) {
        throw takeFromExternrefTable0(ret[1]);
    }
    return takeFromExternrefTable0(ret[0]);
}

/**
 * @param {string} json
 * @returns {number}
 */
export function register_cards(json) {
    const ptr0 = passStringToWasm0(json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len0 = WASM_VECTOR_LEN;
    const ret = wasm.register_cards(ptr0, len0);
    if (ret[2]) {
        throw takeFromExternrefTable0(ret[1]);
    }
    return ret[0] >>> 0;
}

/**
 * @param {string} json
 * @returns {number}
 */
export function register_scripts(json) {
    const ptr0 = passStringToWasm0(json, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
    const len0 = WASM_VECTOR_LEN;
    const ret = wasm.register_scripts(ptr0, len0);
    if (ret[2]) {
        throw takeFromExternrefTable0(ret[1]);
    }
    return ret[0] >>> 0;
}

/**
 * @param {number} duel_id
 * @param {Uint8Array} bytes
 */
export function set_response_bytes(duel_id, bytes) {
    const ret = wasm.set_response_bytes(duel_id, bytes);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}

/**
 * @param {number} duel_id
 * @param {number} value
 */
export function set_response_i(duel_id, value) {
    const ret = wasm.set_response_i(duel_id, value);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}

/**
 * @param {number} duel_id
 */
export function start_duel(duel_id) {
    const ret = wasm.start_duel(duel_id);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}
function __wbg_get_imports() {
    const import0 = {
        __proto__: null,
        __wbg__OCG_CreateDuel_2a79072258b45c9c: function(arg0, arg1, arg2) {
            const ret = arg0._OCG_CreateDuel(arg1 >>> 0, arg2 >>> 0);
            return ret;
        },
        __wbg__OCG_DestroyDuel_4ce1e593dc0819c5: function(arg0, arg1) {
            arg0._OCG_DestroyDuel(arg1 >>> 0);
        },
        __wbg__OCG_DuelGetMessage_422c8617eb8248b2: function(arg0, arg1, arg2) {
            const ret = arg0._OCG_DuelGetMessage(arg1 >>> 0, arg2 >>> 0);
            return ret;
        },
        __wbg__OCG_DuelNewCard_0f80443f618045ca: function(arg0, arg1, arg2) {
            arg0._OCG_DuelNewCard(arg1 >>> 0, arg2 >>> 0);
        },
        __wbg__OCG_DuelProcess_25d797e36a5fca34: function(arg0, arg1) {
            const ret = arg0._OCG_DuelProcess(arg1 >>> 0);
            return ret;
        },
        __wbg__OCG_DuelSetResponse_82bca0f22eefbf44: function(arg0, arg1, arg2, arg3) {
            arg0._OCG_DuelSetResponse(arg1 >>> 0, arg2 >>> 0, arg3 >>> 0);
        },
        __wbg__OCG_GetVersion_58e05cb96f7eefba: function(arg0, arg1, arg2) {
            arg0._OCG_GetVersion(arg1 >>> 0, arg2 >>> 0);
        },
        __wbg__OCG_LoadScript_6dc76fa578ee98cf: function(arg0, arg1, arg2, arg3, arg4) {
            const ret = arg0._OCG_LoadScript(arg1 >>> 0, arg2 >>> 0, arg3 >>> 0, arg4 >>> 0);
            return ret;
        },
        __wbg__OCG_StartDuel_ebe725e6d9651979: function(arg0, arg1) {
            arg0._OCG_StartDuel(arg1 >>> 0);
        },
        __wbg___wbindgen_debug_string_a57024b9c6e4a48b: function(arg0, arg1) {
            const ret = debugString(arg1);
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_is_function_5e4570eb24ffa122: function(arg0) {
            const ret = typeof(arg0) === 'function';
            return ret;
        },
        __wbg___wbindgen_is_undefined_6cff064c44e0d823: function(arg0) {
            const ret = arg0 === undefined;
            return ret;
        },
        __wbg___wbindgen_number_get_136b9679cab35cfb: function(arg0, arg1) {
            const obj = arg1;
            const ret = typeof(obj) === 'number' ? obj : undefined;
            getDataViewMemory0().setFloat64(arg0 + 8 * 1, isLikeNone(ret) ? 0 : ret, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, !isLikeNone(ret), true);
        },
        __wbg___wbindgen_throw_bb96b2010945f0bc: function(arg0, arg1) {
            throw new Error(getStringFromWasm0(arg0, arg1));
        },
        __wbg__free_5488690db1e7fa13: function(arg0, arg1) {
            arg0._free(arg1 >>> 0);
        },
        __wbg__malloc_03572826bc73d43b: function(arg0, arg1) {
            const ret = arg0._malloc(arg1 >>> 0);
            return ret;
        },
        __wbg__wbg_cb_unref_be22cc64ae6946a0: function(arg0) {
            arg0._wbg_cb_unref();
        },
        __wbg_addFunction_4242d2430d4a6d56: function(arg0, arg1, arg2, arg3) {
            const ret = arg0.addFunction(arg1, getStringFromWasm0(arg2, arg3));
            return ret;
        },
        __wbg_buffer_8117fe4dab119813: function(arg0) {
            const ret = arg0.buffer;
            return ret;
        },
        __wbg_byteLength_031910aabf3577e0: function(arg0) {
            const ret = arg0.byteLength;
            return ret;
        },
        __wbg_call_35dba3c747ad7521: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.call(arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_getInt32_e0ef2c9c5c9de661: function(arg0, arg1, arg2) {
            const ret = arg0.getInt32(arg1 >>> 0, arg2 !== 0);
            return ret;
        },
        __wbg_getUint32_0857c69fc30e1cbb: function(arg0, arg1, arg2) {
            const ret = arg0.getUint32(arg1 >>> 0, arg2 !== 0);
            return ret;
        },
        __wbg_get_971a0c45d172643f: function() { return handleError(function (arg0, arg1) {
            const ret = Reflect.get(arg0, arg1);
            return ret;
        }, arguments); },
        __wbg_get_index_692b103434df899b: function(arg0, arg1) {
            const ret = arg0[arg1 >>> 0];
            return ret;
        },
        __wbg_length_36bd29c6848c2144: function(arg0) {
            const ret = arg0.length;
            return ret;
        },
        __wbg_new_13a20857fcf78d7a: function(arg0, arg1, arg2) {
            const ret = new DataView(arg0, arg1 >>> 0, arg2 >>> 0);
            return ret;
        },
        __wbg_new_77cc4f4f472aeb81: function(arg0) {
            const ret = new Uint8Array(arg0);
            return ret;
        },
        __wbg_new_ebe3e0f6837f0879: function() {
            const ret = new Object();
            return ret;
        },
        __wbg_new_from_slice_3eea173078478cfe: function(arg0, arg1) {
            const ret = new Uint8Array(getArrayU8FromWasm0(arg0, arg1));
            return ret;
        },
        __wbg_new_typed_cceaf62d8d95e9f2: function(arg0, arg1) {
            try {
                var state0 = {a: arg0, b: arg1};
                var cb0 = (arg0, arg1) => {
                    const a = state0.a;
                    state0.a = 0;
                    try {
                        return wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined_______true_(a, state0.b, arg0, arg1);
                    } finally {
                        state0.a = a;
                    }
                };
                const ret = new Promise(cb0);
                return ret;
            } finally {
                state0.a = 0;
            }
        },
        __wbg_new_with_byte_offset_and_length_ff6e927f8d72f0c3: function(arg0, arg1, arg2) {
            const ret = new Uint8Array(arg0, arg1 >>> 0, arg2 >>> 0);
            return ret;
        },
        __wbg_new_with_length_3ffc1c56427c525c: function(arg0) {
            const ret = new Uint8Array(arg0 >>> 0);
            return ret;
        },
        __wbg_now_8b265300afd5f2b9: function() {
            const ret = Date.now();
            return ret;
        },
        __wbg_prototypesetcall_de8e0d9553586985: function(arg0, arg1, arg2) {
            Uint8Array.prototype.set.call(getArrayU8FromWasm0(arg0, arg1), arg2);
        },
        __wbg_queueMicrotask_ac694eae12e92dfb: function(arg0) {
            queueMicrotask(arg0);
        },
        __wbg_queueMicrotask_be5fe34a8f4cad4d: function(arg0) {
            const ret = arg0.queueMicrotask;
            return ret;
        },
        __wbg_random_b0d98802be10ff20: function() {
            const ret = Math.random();
            return ret;
        },
        __wbg_resolve_020f95d838c6ef25: function(arg0) {
            const ret = Promise.resolve(arg0);
            return ret;
        },
        __wbg_set_8155bb79a948541b: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = Reflect.set(arg0, arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_set_862c439a342a8818: function(arg0, arg1, arg2) {
            arg0.set(arg1, arg2 >>> 0);
        },
        __wbg_static_accessor_GLOBAL_THIS_466428f93b4eaa76: function() {
            const ret = typeof globalThis === 'undefined' ? null : globalThis;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        },
        __wbg_static_accessor_GLOBAL_c7aea38d4de089bc: function() {
            const ret = typeof global === 'undefined' ? null : global;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        },
        __wbg_static_accessor_SELF_42d4fae05e59267a: function() {
            const ret = typeof self === 'undefined' ? null : self;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        },
        __wbg_static_accessor_WINDOW_e0db14a0eba6a812: function() {
            const ret = typeof window === 'undefined' ? null : window;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        },
        __wbg_then_7026b513a94278a8: function(arg0, arg1) {
            const ret = arg0.then(arg1);
            return ret;
        },
        __wbg_then_72819b8d4e081fb5: function(arg0, arg1, arg2) {
            const ret = arg0.then(arg1, arg2);
            return ret;
        },
        __wbg_wasmMemory_eed462b6a2b0df82: function(arg0) {
            const ret = arg0.wasmMemory;
            return ret;
        },
        __wbindgen_cast_0000000000000001: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [Externref], shim_idx: 90, ret: Result(Unit), inner_ret: Some(Result(Unit)) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue__core_ed718c3d60ebd546___result__Result_____wasm_bindgen_d1a1f5b9c1e1d7e3___JsError___true_);
            return ret;
        },
        __wbindgen_cast_0000000000000002: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [U32, U32, I32], shim_idx: 48, ret: Unit, inner_ret: Some(Unit) }, mutable: false }) -> Externref`.
            const ret = makeClosure(arg0, arg1, wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true_);
            return ret;
        },
        __wbindgen_cast_0000000000000003: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [U32, U32, U32], shim_idx: 48, ret: Unit, inner_ret: Some(Unit) }, mutable: false }) -> Externref`.
            const ret = makeClosure(arg0, arg1, wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true__2);
            return ret;
        },
        __wbindgen_cast_0000000000000004: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [U32, U32, U32], shim_idx: 50, ret: I32, inner_ret: Some(I32) }, mutable: false }) -> Externref`.
            const ret = makeClosure(arg0, arg1, wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__u32__i32__true_);
            return ret;
        },
        __wbindgen_cast_0000000000000005: function(arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { owned: true, function: Function { arguments: [U32, U32], shim_idx: 46, ret: Unit, inner_ret: Some(Unit) }, mutable: false }) -> Externref`.
            const ret = makeClosure(arg0, arg1, wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32______true_);
            return ret;
        },
        __wbindgen_cast_0000000000000006: function(arg0) {
            // Cast intrinsic for `F64 -> Externref`.
            const ret = arg0;
            return ret;
        },
        __wbindgen_cast_0000000000000007: function(arg0, arg1) {
            // Cast intrinsic for `Ref(String) -> Externref`.
            const ret = getStringFromWasm0(arg0, arg1);
            return ret;
        },
        __wbindgen_init_externref_table: function() {
            const table = wasm.__wbindgen_externrefs;
            const offset = table.grow(4);
            table.set(0, undefined);
            table.set(offset + 0, undefined);
            table.set(offset + 1, null);
            table.set(offset + 2, true);
            table.set(offset + 3, false);
        },
    };
    return {
        __proto__: null,
        "./duellab_engine_bg.js": import0,
        "./snippets/ocgcore-ffi-c6e3cc3310618123/ocgcore.js": import1,
    };
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue__core_ed718c3d60ebd546___result__Result_____wasm_bindgen_d1a1f5b9c1e1d7e3___JsError___true_(arg0, arg1, arg2) {
    const ret = wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue__core_ed718c3d60ebd546___result__Result_____wasm_bindgen_d1a1f5b9c1e1d7e3___JsError___true_(arg0, arg1, arg2);
    if (ret[1]) {
        throw takeFromExternrefTable0(ret[0]);
    }
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined_______true_(arg0, arg1, arg2, arg3) {
    wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined___js_sys_3433103401833a38___Function_fn_wasm_bindgen_d1a1f5b9c1e1d7e3___JsValue_____wasm_bindgen_d1a1f5b9c1e1d7e3___sys__Undefined_______true_(arg0, arg1, arg2, arg3);
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32______true_(arg0, arg1, arg2, arg3) {
    wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32______true_(arg0, arg1, arg2, arg3);
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true_(arg0, arg1, arg2, arg3, arg4) {
    wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true_(arg0, arg1, arg2, arg3, arg4);
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true__2(arg0, arg1, arg2, arg3, arg4) {
    wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__i32______true__2(arg0, arg1, arg2, arg3, arg4);
}

function wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__u32__i32__true_(arg0, arg1, arg2, arg3, arg4) {
    const ret = wasm.wasm_bindgen_d1a1f5b9c1e1d7e3___convert__closures_____invoke___u32__u32__u32__i32__true_(arg0, arg1, arg2, arg3, arg4);
    return ret;
}

function addToExternrefTable0(obj) {
    const idx = wasm.__externref_table_alloc();
    wasm.__wbindgen_externrefs.set(idx, obj);
    return idx;
}

const CLOSURE_DTORS = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(state => wasm.__wbindgen_destroy_closure(state.a, state.b));

function debugString(val) {
    // primitive types
    const type = typeof val;
    if (type == 'number' || type == 'boolean' || val == null) {
        return  `${val}`;
    }
    if (type == 'string') {
        return `"${val}"`;
    }
    if (type == 'symbol') {
        const description = val.description;
        if (description == null) {
            return 'Symbol';
        } else {
            return `Symbol(${description})`;
        }
    }
    if (type == 'function') {
        const name = val.name;
        if (typeof name == 'string' && name.length > 0) {
            return `Function(${name})`;
        } else {
            return 'Function';
        }
    }
    // objects
    if (Array.isArray(val)) {
        const length = val.length;
        let debug = '[';
        if (length > 0) {
            debug += debugString(val[0]);
        }
        for(let i = 1; i < length; i++) {
            debug += ', ' + debugString(val[i]);
        }
        debug += ']';
        return debug;
    }
    // Test for built-in
    const builtInMatches = /\[object ([^\]]+)\]/.exec(toString.call(val));
    let className;
    if (builtInMatches && builtInMatches.length > 1) {
        className = builtInMatches[1];
    } else {
        // Failed to match the standard '[object ClassName]'
        return toString.call(val);
    }
    if (className == 'Object') {
        // we're a user defined class or Object
        // JSON.stringify avoids problems with cycles, and is generally much
        // easier than looping through ownProperties of `val`.
        try {
            return 'Object(' + JSON.stringify(val) + ')';
        } catch (_) {
            return 'Object';
        }
    }
    // errors
    if (val instanceof Error) {
        return `${val.name}: ${val.message}\n${val.stack}`;
    }
    // TODO we could test for more things here, like `Set`s and `Map`s.
    return className;
}

function getArrayU8FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint8ArrayMemory0().subarray(ptr / 1, ptr / 1 + len);
}

let cachedDataViewMemory0 = null;
function getDataViewMemory0() {
    if (cachedDataViewMemory0 === null || cachedDataViewMemory0.buffer.detached === true || (cachedDataViewMemory0.buffer.detached === undefined && cachedDataViewMemory0.buffer !== wasm.memory.buffer)) {
        cachedDataViewMemory0 = new DataView(wasm.memory.buffer);
    }
    return cachedDataViewMemory0;
}

function getStringFromWasm0(ptr, len) {
    return decodeText(ptr >>> 0, len);
}

let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0.byteLength === 0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm.memory.buffer);
    }
    return cachedUint8ArrayMemory0;
}

function handleError(f, args) {
    try {
        return f.apply(this, args);
    } catch (e) {
        const idx = addToExternrefTable0(e);
        wasm.__wbindgen_exn_store(idx);
    }
}

function isLikeNone(x) {
    return x === undefined || x === null;
}

function makeClosure(arg0, arg1, f) {
    const state = { a: arg0, b: arg1, cnt: 1 };
    const real = (...args) => {

        // First up with a closure we increment the internal reference
        // count. This ensures that the Rust closure environment won't
        // be deallocated while we're invoking it.
        state.cnt++;
        try {
            return f(state.a, state.b, ...args);
        } finally {
            real._wbg_cb_unref();
        }
    };
    real._wbg_cb_unref = () => {
        if (--state.cnt === 0) {
            wasm.__wbindgen_destroy_closure(state.a, state.b);
            state.a = 0;
            CLOSURE_DTORS.unregister(state);
        }
    };
    CLOSURE_DTORS.register(real, state, state);
    return real;
}

function makeMutClosure(arg0, arg1, f) {
    const state = { a: arg0, b: arg1, cnt: 1 };
    const real = (...args) => {

        // First up with a closure we increment the internal reference
        // count. This ensures that the Rust closure environment won't
        // be deallocated while we're invoking it.
        state.cnt++;
        const a = state.a;
        state.a = 0;
        try {
            return f(a, state.b, ...args);
        } finally {
            state.a = a;
            real._wbg_cb_unref();
        }
    };
    real._wbg_cb_unref = () => {
        if (--state.cnt === 0) {
            wasm.__wbindgen_destroy_closure(state.a, state.b);
            state.a = 0;
            CLOSURE_DTORS.unregister(state);
        }
    };
    CLOSURE_DTORS.register(real, state, state);
    return real;
}

function passStringToWasm0(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = cachedTextEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8ArrayMemory0().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8ArrayMemory0();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 0x7F) break;
        mem[ptr + offset] = code;
    }
    if (offset !== len) {
        if (offset !== 0) {
            arg = arg.slice(offset);
        }
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8ArrayMemory0().subarray(ptr + offset, ptr + len);
        const ret = cachedTextEncoder.encodeInto(arg, view);

        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

function takeFromExternrefTable0(idx) {
    const value = wasm.__wbindgen_externrefs.get(idx);
    wasm.__externref_table_dealloc(idx);
    return value;
}

let cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
cachedTextDecoder.decode();
const MAX_SAFARI_DECODE_BYTES = 2146435072;
let numBytesDecoded = 0;
function decodeText(ptr, len) {
    numBytesDecoded += len;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
        cachedTextDecoder.decode();
        numBytesDecoded = len;
    }
    return cachedTextDecoder.decode(getUint8ArrayMemory0().subarray(ptr, ptr + len));
}

const cachedTextEncoder = new TextEncoder();

if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder.encodeInto = function (arg, view) {
        const buf = cachedTextEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };
}

let WASM_VECTOR_LEN = 0;

let wasmModule, wasmInstance, wasm;
function __wbg_finalize_init(instance, module) {
    wasmInstance = instance;
    wasm = instance.exports;
    wasmModule = module;
    cachedDataViewMemory0 = null;
    cachedUint8ArrayMemory0 = null;
    wasm.__wbindgen_start();
    return wasm;
}

async function __wbg_load(module, imports) {
    if (typeof Response === 'function' && module instanceof Response) {
        if (!module.ok) {
            throw new Error(`failed to fetch Wasm: ${module.status} ${module.statusText} fetching '${module.url}'`);
        }

        if (typeof WebAssembly.instantiateStreaming === 'function') {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                const validResponse = expectedResponseType(module.type);

                if (validResponse && module.headers.get('Content-Type') !== 'application/wasm') {
                    console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", e);

                } else { throw e; }
            }
        }

        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);

        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }

    function expectedResponseType(type) {
        switch (type) {
            case 'basic': case 'cors': case 'default': return true;
        }
        return false;
    }
}

function initSync(module) {
    if (wasm !== undefined) return wasm;


    if (module !== undefined) {
        if (Object.getPrototypeOf(module) === Object.prototype) {
            ({module} = module)
        } else {
            console.warn('using deprecated parameters for `initSync()`; pass a single object instead')
        }
    }

    const imports = __wbg_get_imports();
    if (!(module instanceof WebAssembly.Module)) {
        module = new WebAssembly.Module(module);
    }
    const instance = new WebAssembly.Instance(module, imports);
    return __wbg_finalize_init(instance, module);
}

async function __wbg_init(module_or_path) {
    if (wasm !== undefined) return wasm;


    if (module_or_path !== undefined) {
        if (Object.getPrototypeOf(module_or_path) === Object.prototype) {
            ({module_or_path} = module_or_path)
        } else {
            console.warn('using deprecated parameters for the initialization function; pass a single object instead')
        }
    }

    if (module_or_path === undefined) {
        module_or_path = new URL('duellab_engine_bg.wasm', import.meta.url);
    }
    const imports = __wbg_get_imports();

    if (typeof module_or_path === 'string' || (typeof Request === 'function' && module_or_path instanceof Request) || (typeof URL === 'function' && module_or_path instanceof URL)) {
        module_or_path = fetch(module_or_path);
    }

    const { instance, module } = await __wbg_load(await module_or_path, imports);

    return __wbg_finalize_init(instance, module);
}

export { initSync, __wbg_init as default };
