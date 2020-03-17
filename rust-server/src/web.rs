use actix_web::{error, get, web, App, HttpResponse, HttpServer, Result, post};
use anyhow::Context;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::fmt::Display;

use crate::db;

#[derive(Debug)]
struct AppError(anyhow::Error);

impl error::ResponseError for AppError {}
impl Display for AppError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "internal server errror")
    }
}

#[derive(Debug, Serialize, Deserialize)]
struct Video {
    id: String,
    url: String,
}

#[get("/{chat_name}")]
async fn playlist(chat_name: web::Path<String>) -> Result<HttpResponse> {
    let db = sled::open("db.sled").map_err(|_| error::ErrorInternalServerError(""))?;
    let queue = db::get_or_create_queue(&db, &chat_name).map_err(|_| error::ErrorInternalServerError(""))?;
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

#[derive(Debug, Serialize, Deserialize)]
struct PoppedResponse {
    popped: Uuid
}

#[post("/{chat_name}/pop")]
async fn pop(chat_name: web::Path<String>) -> Result<HttpResponse> {
    let db = sled::open("db.sled").map_err(|_| error::ErrorInternalServerError(""))?;
    let queue = db::get_or_create_queue(&db, &chat_name).map_err(|_| error::ErrorInternalServerError(""))?;
    Ok(HttpResponse::Ok().json(PoppedResponse {
        popped: Uuid::default()
    }))
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
