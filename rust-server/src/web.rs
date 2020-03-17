use actix_web::{error, get, web, App, Error, HttpResponse, HttpServer, Responder, Result};
use anyhow::Context;
use serde::{Deserialize, Serialize};

use crate::db;

#[derive(Debug, Serialize, Deserialize)]
struct Video {
    id: String,
    url: String,
}

#[get("/{chat_name}/next")]
async fn next(info: web::Path<String>) -> impl Responder {
    format!("Hello {}!", info)
}

#[get("/{chat_name}")]
async fn playlist(chat_name: web::Path<String>) -> Result<HttpResponse> {
    let db = sled::open("db.sled").map_err(|err| error::ErrorInternalServerError(""))?;
    let queue = db::get_or_create_queue(&db, &chat_name).map_err(|_| error::ErrorInternalServerError(""))?;
    let items: Vec<Video> = queue.iter().map(|(id, url)| {
        Video {
            url: url.clone(),
            id: id.to_string(),
        }
    }).collect();
    Ok(HttpResponse::Ok().json(items))
}

#[get("/{chat_name}/pop")]
async fn pop(info: web::Path<(u32, String)>) -> impl Responder {
    format!("Hello {}! id:{}", info.1, info.0)
}

pub async fn run() -> anyhow::Result<()> {
    HttpServer::new(|| {
        App::new()
            .data(web::JsonConfig::default())
            .service(playlist)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
    .context("couldnt start server")
}
