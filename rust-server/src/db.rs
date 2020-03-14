use sled;
use uuid::Uuid;
use anyhow::{anyhow, Context, Result};
use bincode;
use names;

pub fn get_or_create_queue(db: &sled::Db, chat_name: &str) -> Result<Vec<(Uuid, String)>> {
    match db.get(&chat_name)? {
        Some(bytes) => bincode::deserialize(&bytes).context("Can't deserialize queue from db"),
        None => Ok(Vec::new()),
    }
}

pub fn get_or_create_chat_name(chat_id: i64, tree: &sled::Db) -> Result<String> {
    let chat_name_key = format!("name_{}", chat_id);
    match tree.get(&chat_name_key)? {
        Some(name) => String::from_utf8(name.to_vec()).context("Can't decode name"),
        None => {
            let new_name = names::Generator::default()
                .next()
                .ok_or(anyhow!("Couldn't generate new name"))?;
            tree.insert(&chat_name_key, new_name.clone().into_bytes())?;
            Ok(new_name)
        }
    }
}
