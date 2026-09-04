use std::cell::RefCell;
use std::collections::HashMap;
use std::ffi::{c_char, c_void, CStr, CString};
use std::ptr::null_mut;

use js_sys::{Object, Reflect, Uint8Array};
use ocgcore_ffi::types::{
    OCG_CardData, OCG_Duel, OCG_DuelOptions, OCG_NewCardInfo, OCG_Player,
};
use ocgcore_ffi::{
    initialize, OCG_CreateDuel, OCG_DestroyDuel, OCG_DuelGetMessage, OCG_DuelNewCard,
    OCG_DuelProcess, OCG_DuelSetResponse, OCG_GetVersion, OCG_LoadScript, OCG_StartDuel,
};
use serde::Deserialize;
use wasm_bindgen::prelude::*;

const POS_FACEDOWN_DEFENSE: u32 = 0x8;
const DUEL_MODE_MR5: u64 = 0x2E800;
const DUEL_SIMPLE_AI: u64 = 0x40;

#[derive(Debug, Deserialize)]
struct CardRecordInput {
    id: u32,
    #[serde(default)]
    alias: u32,
    #[serde(default)]
    setcode: String,
    #[serde(rename = "type", default)]
    card_type: u32,
    #[serde(default)]
    atk: i32,
    #[serde(default)]
    def: i32,
    #[serde(default)]
    level: u32,
    #[serde(default)]
    race: String,
    #[serde(default)]
    attribute: u32,
}

struct CardRecordOwned {
    code: u32,
    alias: u32,
    setcodes: Box<[u16]>,
    card_type: u32,
    level: u32,
    attribute: u32,
    race: u64,
    attack: i32,
    defense: i32,
    lscale: u32,
    rscale: u32,
    link_marker: u32,
}

thread_local! {
    static CARDS: RefCell<HashMap<u32, CardRecordOwned>> = RefCell::new(HashMap::new());
    static SCRIPTS: RefCell<HashMap<String, String>> = RefCell::new(HashMap::new());
    static DUELS: RefCell<HashMap<u32, OCG_Duel>> = RefCell::new(HashMap::new());
    static NEXT_DUEL_ID: RefCell<u32> = const { RefCell::new(1) };
}

fn set(obj: &Object, key: &str, value: JsValue) {
    let _ = Reflect::set(obj, &JsValue::from_str(key), &value);
}

fn parse_u64_text(value: &str) -> u64 {
    let s = value.trim();
    if s.is_empty() {
        return 0;
    }
    if let Some(hex) = s.strip_prefix("0x").or_else(|| s.strip_prefix("0X")) {
        u64::from_str_radix(hex, 16).unwrap_or(0)
    } else {
        s.parse::<u64>().unwrap_or(0)
    }
}

fn split_setcodes(value: u64) -> Box<[u16]> {
    let mut out = Vec::with_capacity(5);
    for shift in [0, 16, 32, 48] {
        let code = ((value >> shift) & 0xffff) as u16;
        if code != 0 {
            out.push(code);
        }
    }
    out.push(0);
    out.into_boxed_slice()
}

unsafe extern "C" fn card_reader(_payload: *mut c_void, code: u32, data: *mut OCG_CardData) {
    if data.is_null() {
        return;
    }
    CARDS.with(|cards| {
        if let Some(card) = cards.borrow().get(&code) {
            unsafe {
                *data = OCG_CardData {
                    code: card.code,
                    alias: card.alias,
                    setcodes: card.setcodes.as_ptr() as *mut u16,
                    r#type: card.card_type,
                    level: card.level,
                    attribute: card.attribute,
                    race: card.race,
                    attack: card.attack,
                    defense: card.defense,
                    lscale: card.lscale,
                    rscale: card.rscale,
                    link_marker: card.link_marker,
                };
            }
        } else {
            unsafe {
                *data = OCG_CardData {
                    code,
                    alias: 0,
                    setcodes: null_mut(),
                    r#type: 0,
                    level: 0,
                    attribute: 0,
                    race: 0,
                    attack: 0,
                    defense: 0,
                    lscale: 0,
                    rscale: 0,
                    link_marker: 0,
                };
            }
        }
    });
}

unsafe extern "C" fn card_reader_done(_payload: *mut c_void, _data: *mut OCG_CardData) {}

unsafe extern "C" fn script_reader(
    _payload: *mut c_void,
    duel: OCG_Duel,
    name_ptr: *const c_char,
) -> i32 {
    if name_ptr.is_null() {
        return 0;
    }
    let requested = unsafe { CStr::from_ptr(name_ptr) }.to_string_lossy().to_string();
    let basename = requested.rsplit('/').next().unwrap_or(&requested).to_string();
    let source = SCRIPTS.with(|scripts| {
        let scripts = scripts.borrow();
        scripts
            .get(&requested)
            .or_else(|| scripts.get(&basename))
            .cloned()
    });
    let Some(source) = source else {
        return 0;
    };
    let Ok(cname) = CString::new(requested) else {
        return 0;
    };
    unsafe {
        OCG_LoadScript(
            duel,
            source.as_ptr() as *const c_char,
            source.len() as u32,
            cname.as_ptr(),
        )
    }
}

unsafe extern "C" fn log_handler(
    _payload: *mut c_void,
    _string: *const c_char,
    _log_type: i32,
) {
}

fn with_duel<R>(id: u32, f: impl FnOnce(OCG_Duel) -> R) -> Result<R, JsValue> {
    DUELS.with(|duels| {
        let map = duels.borrow();
        let duel = map
            .get(&id)
            .copied()
            .ok_or_else(|| JsValue::from_str("Duel handle not found"))?;
        Ok(f(duel))
    })
}

#[wasm_bindgen]
pub async fn init_engine() -> Result<JsValue, JsValue> {
    initialize().await;

    let mut major = 0i32;
    let mut minor = 0i32;
    OCG_GetVersion(&mut major, &mut minor);

    let out = Object::new();
    set(&out, "ok", JsValue::TRUE);
    set(&out, "coreInitialized", JsValue::TRUE);
    set(&out, "major", JsValue::from_f64(major as f64));
    set(&out, "minor", JsValue::from_f64(minor as f64));
    set(&out, "version", JsValue::from_str(&format!("{}.{}", major, minor)));
    Ok(out.into())
}

#[wasm_bindgen]
pub fn register_cards(json: &str) -> Result<u32, JsValue> {
    let records: Vec<CardRecordInput> =
        serde_json::from_str(json).map_err(|e| JsValue::from_str(&format!("card json: {e}")))?;

    let mut count = 0u32;
    CARDS.with(|cards| {
        let mut map = cards.borrow_mut();
        for input in records {
            let level_raw = input.level;
            let level = level_raw & 0xff;
            let lscale = (level_raw >> 24) & 0xff;
            let rscale = (level_raw >> 16) & 0xff;
            let setcode = parse_u64_text(&input.setcode);
            let race = parse_u64_text(&input.race);
            let link_marker = if input.card_type & 0x4000000 != 0 {
                input.def.max(0) as u32
            } else {
                0
            };

            map.insert(
                input.id,
                CardRecordOwned {
                    code: input.id,
                    alias: input.alias,
                    setcodes: split_setcodes(setcode),
                    card_type: input.card_type,
                    level,
                    attribute: input.attribute,
                    race,
                    attack: input.atk,
                    defense: input.def,
                    lscale,
                    rscale,
                    link_marker,
                },
            );
            count += 1;
        }
    });
    Ok(count)
}

#[wasm_bindgen]
pub fn clear_registered_cards() {
    CARDS.with(|cards| cards.borrow_mut().clear());
}

#[wasm_bindgen]
pub fn register_scripts(json: &str) -> Result<u32, JsValue> {
    let values: HashMap<String, String> =
        serde_json::from_str(json).map_err(|e| JsValue::from_str(&format!("script json: {e}")))?;
    let count = values.len() as u32;
    SCRIPTS.with(|scripts| {
        let mut map = scripts.borrow_mut();
        for (name, source) in values {
            let base = name.rsplit('/').next().unwrap_or(&name).to_string();
            map.insert(name, source.clone());
            map.insert(base, source);
        }
    });
    Ok(count)
}

#[wasm_bindgen]
pub fn clear_registered_scripts() {
    SCRIPTS.with(|scripts| scripts.borrow_mut().clear());
}

#[wasm_bindgen]
pub fn create_duel(extra_flags: u32) -> Result<u32, JsValue> {
    let player = OCG_Player {
        starting_lp: 8000,
        starting_draw_count: 5,
        draw_count_per_turn: 1,
    };

    let options = OCG_DuelOptions {
        seed: [
            0x53455254414f5443,
            0x4455454c4c414230,
            js_sys::Date::now() as u64,
            (js_sys::Math::random() * u32::MAX as f64) as u64,
        ],
        flags: DUEL_MODE_MR5 | DUEL_SIMPLE_AI | extra_flags as u64,
        team1: player,
        team2: player,
        cardReader: Some(card_reader),
        payload1: null_mut(),
        scriptReader: Some(script_reader),
        payload2: null_mut(),
        logHandler: Some(log_handler),
        payload3: null_mut(),
        cardReaderDone: Some(card_reader_done),
        payload4: null_mut(),
        enableUnsafeLibraries: 0,
    };

    let mut duel: OCG_Duel = null_mut();
    let status = unsafe { OCG_CreateDuel(&mut duel, &options) };
    if status != 0 || duel.is_null() {
        return Err(JsValue::from_str(&format!("OCG_CreateDuel failed: {status}")));
    }

    let id = NEXT_DUEL_ID.with(|next| {
        let mut value = next.borrow_mut();
        let id = *value;
        *value = value.wrapping_add(1).max(1);
        id
    });
    DUELS.with(|duels| {
        duels.borrow_mut().insert(id, duel);
    });
    Ok(id)
}

#[wasm_bindgen]
pub fn load_script(duel_id: u32, name: &str, source: &str) -> Result<bool, JsValue> {
    let cname = CString::new(name).map_err(|_| JsValue::from_str("Invalid script name"))?;
    let bytes = source.as_bytes();
    with_duel(duel_id, |duel| unsafe {
        OCG_LoadScript(
            duel,
            bytes.as_ptr() as *const c_char,
            bytes.len() as u32,
            cname.as_ptr(),
        ) > 0
    })
}

#[wasm_bindgen]
pub fn add_card(duel_id: u32, team: u8, code: u32, location: u32) -> Result<(), JsValue> {
    let info = OCG_NewCardInfo {
        team,
        duelist: 0,
        code,
        con: team,
        loc: location,
        seq: 0,
        pos: POS_FACEDOWN_DEFENSE,
    };
    with_duel(duel_id, |duel| unsafe {
        OCG_DuelNewCard(duel, &info);
    })
}

#[wasm_bindgen]
pub fn start_duel(duel_id: u32) -> Result<(), JsValue> {
    with_duel(duel_id, |duel| unsafe {
        let _ = OCG_StartDuel(duel);
    })
}

#[wasm_bindgen]
pub fn process_duel(duel_id: u32) -> Result<JsValue, JsValue> {
    with_duel(duel_id, |duel| unsafe {
        let status = OCG_DuelProcess(duel);
        let mut length = 0u32;
        let ptr = OCG_DuelGetMessage(duel, &mut length);
        let out = Object::new();
        set(&out, "status", JsValue::from_f64(status as f64));
        if !ptr.is_null() && length > 0 {
            let slice = std::slice::from_raw_parts(ptr as *const u8, length as usize);
            let arr = Uint8Array::from(slice);
            set(&out, "message", arr.into());
            set(&out, "length", JsValue::from_f64(length as f64));
        } else {
            set(&out, "message", Uint8Array::new_with_length(0).into());
            set(&out, "length", JsValue::from_f64(0.0));
        }
        out.into()
    })
}

#[wasm_bindgen]
pub fn set_response_i(duel_id: u32, value: i32) -> Result<(), JsValue> {
    let bytes = value.to_le_bytes();
    with_duel(duel_id, |duel| unsafe {
        OCG_DuelSetResponse(duel, bytes.as_ptr() as *const c_void, bytes.len() as u32);
    })
}

#[wasm_bindgen]
pub fn set_response_bytes(duel_id: u32, bytes: Uint8Array) -> Result<(), JsValue> {
    let vec = bytes.to_vec();
    with_duel(duel_id, |duel| unsafe {
        OCG_DuelSetResponse(duel, vec.as_ptr() as *const c_void, vec.len() as u32);
    })
}

#[wasm_bindgen]
pub fn destroy_duel(duel_id: u32) -> Result<(), JsValue> {
    let duel = DUELS.with(|duels| duels.borrow_mut().remove(&duel_id));
    if let Some(duel) = duel {
        unsafe { OCG_DestroyDuel(duel) };
        Ok(())
    } else {
        Err(JsValue::from_str("Duel handle not found"))
    }
}

#[wasm_bindgen]
pub fn bridge_version() -> String {
    "sertaotcg-duellab-ocgcore-bridge/0.3.0".to_string()
}
