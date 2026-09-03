use std::ffi::c_void;
use std::ptr::null_mut;

use js_sys::{Object, Reflect};
use ocgcore_ffi::types::{OCG_Duel, OCG_DuelOptions, OCG_Player};
use ocgcore_ffi::{initialize, OCG_CreateDuel, OCG_DestroyDuel, OCG_GetVersion};
use wasm_bindgen::prelude::*;

fn set(obj: &Object, key: &str, value: JsValue) {
    let _ = Reflect::set(obj, &JsValue::from_str(key), &value);
}

#[wasm_bindgen]
pub async fn init_engine() -> Result<JsValue, JsValue> {
    initialize().await;

    let mut major = 0i32;
    let mut minor = 0i32;
    OCG_GetVersion(&mut major, &mut minor);

    let player = OCG_Player {
        starting_lp: 8000,
        starting_draw_count: 5,
        draw_count_per_turn: 1,
    };

    let options = OCG_DuelOptions {
        seed: [0x53455254414f5443, 0x4455454c4c414230, 0x0000000000000001, 0x0000000000000002],
        flags: 0,
        team1: player,
        team2: player,
        cardReader: None,
        payload1: null_mut::<c_void>(),
        scriptReader: None,
        payload2: null_mut::<c_void>(),
        logHandler: None,
        payload3: null_mut::<c_void>(),
        cardReaderDone: None,
        payload4: null_mut::<c_void>(),
        enableUnsafeLibraries: 0,
    };

    let mut duel: OCG_Duel = null_mut();
    let status = unsafe { OCG_CreateDuel(&mut duel, &options) };
    let duel_created = status == 0 && !duel.is_null();

    if duel_created {
        unsafe { OCG_DestroyDuel(duel) };
    }

    let out = Object::new();
    set(&out, "ok", JsValue::from_bool(duel_created));
    set(&out, "coreInitialized", JsValue::TRUE);
    set(&out, "duelCreated", JsValue::from_bool(duel_created));
    set(&out, "createStatus", JsValue::from_f64(status as f64));
    set(&out, "major", JsValue::from_f64(major as f64));
    set(&out, "minor", JsValue::from_f64(minor as f64));
    set(
        &out,
        "version",
        JsValue::from_str(&format!("{}.{}", major, minor)),
    );

    Ok(out.into())
}

#[wasm_bindgen]
pub fn bridge_version() -> String {
    "sertaotcg-duellab-ocgcore-bridge/0.1.0".to_string()
}
