//! Instance-owned storage supplied by an embedding host. Never falls back to browser storage.
use js_sys::{Function, Reflect, Uint8Array};
use ruffle_core::backend::storage::StorageBackend;
use wasm_bindgen::prelude::*;

#[derive(Debug, Clone)]
pub struct HostStorageBackend {
    object: JsValue,
    get: Function,
    put: Function,
    remove: Function,
}

impl HostStorageBackend {
    pub fn new(object: JsValue) -> Result<Self, JsValue> {
        let method = |name: &str| -> Result<Function, JsValue> {
            Reflect::get(&object, &JsValue::from_str(name))?
                .dyn_into::<Function>()
                .map_err(|_| JsValue::from_str("RUFFLE_HOST_STORAGE_INVALID"))
        };
        Ok(Self {
            get: method("get")?,
            put: method("put")?,
            remove: method("remove")?,
            object,
        })
    }
}

impl StorageBackend for HostStorageBackend {
    fn get(&self, name: &str) -> Option<Vec<u8>> {
        let value = self
            .get
            .call1(&self.object, &JsValue::from_str(name))
            .ok()?;
        value
            .dyn_into::<Uint8Array>()
            .ok()
            .map(|bytes| bytes.to_vec())
    }

    fn put(&mut self, name: &str, value: &[u8]) -> bool {
        self.put
            .call2(
                &self.object,
                &JsValue::from_str(name),
                &Uint8Array::from(value),
            )
            .ok()
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
    }

    fn remove_key(&mut self, name: &str) {
        let _ = self.remove.call1(&self.object, &JsValue::from_str(name));
    }
}
