use dotenv::dotenv;
use teloxide::prelude::*;
use tokio;

mod web;
mod bot;
mod db;

#[actix_rt::main]
async fn main() {
    dotenv().expect("please create an .env file");
    run().await;
}

async fn run() {
    teloxide::enable_logging!();

    let bot_instance = Bot::from_env();

    tokio::select! {
        _ = bot::run(bot_instance) => {},
        _ = web::run() => {}
    }
}
