use actix_web::{get, web, App, HttpServer, Responder};
use anyhow::{Result, Context};

#[get("/{chat_name}/next")]
async fn next(info: web::Path<String>) -> impl Responder {
    format!("Hello {}!", info)
}

#[get("/{chat_name}")]
async fn playlist(info: web::Path<(u32, String)>) -> impl Responder {
    format!("Hello {}! id:{}", info.1, info.0)
}

#[get("/{chat_name}/current")]
async fn current(info: web::Path<(u32, String)>) -> impl Responder {
    format!("Hello {}! id:{}", info.1, info.0)
}

#[get("/{chat_name}/pop")]
async fn pop(info: web::Path<(u32, String)>) -> impl Responder {
    format!("Hello {}! id:{}", info.1, info.0)
}

pub async fn run() -> Result<()> {
    HttpServer::new(|| App::new().service(next).service(playlist))
        .bind("127.0.0.1:8080")?
        .run()
        .await.context("couldn't start server")
}
