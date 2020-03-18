use actix_web::{error, get, web, App, HttpResponse, HttpServer, post};
use anyhow::Context;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use thiserror::Error;

use crate::db;

#[derive(Debug, Error)]
#[error("Internal Server Error")]
struct AppError (#[from] anyhow::Error);

impl error::ResponseError for AppError {}

#[derive(Debug, Serialize, Deserialize)]
struct Video {
    id: String,
    url: String,
}

#[get("/{chat_name}")]
async fn playlist(chat_name: web::Path<String>) -> Result<HttpResponse, AppError> {
    let db = sled::open("db.sled").context("couldn't open db")?;
    let queue = db::get_or_create_queue(&db, &chat_name)?;
    let items: Vec<Video> = queue.iter().map(|(id, url)| {
        Video {
            url: url.clone(),
            id: id.to_string(),
        }
    }).collect();
    Ok(HttpResponse::Ok().json(items))
}

#[derive(Debug, Serialize, Deserialize)]
struct PopRequest {
    id: Uuid
}

#[post("/{chat_name}/pop")]
async fn pop(chat_name: web::Path<String>, req: web::Json<PopRequest>) -> Result<HttpResponse, AppError> {
    let db = sled::open("db.sled").context("couldn't open db")?;
    let mut queue = db::get_or_create_queue(&db, &chat_name)?;
    if !queue.iter().any(|entry| entry.0 == req.id) {
        return Ok(HttpResponse::BadRequest().finish())
    }

    match queue.pop() {
        Some (_) => {}
        None => return Ok(HttpResponse::NotFound().finish())
    }

    let serialized = bincode::serialize(&queue).context("failed to serialize queue")?;
    db.insert(&chat_name.as_str(), serialized).context("couldn't write to db")?;

    Ok(HttpResponse::Ok().finish())
}

pub async fn run() -> anyhow::Result<()> {
    HttpServer::new(|| {
        App::new()
            .data(web::JsonConfig::default())
            .service(playlist)
            .service(pop)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
    .context("couldnt start server")
}
