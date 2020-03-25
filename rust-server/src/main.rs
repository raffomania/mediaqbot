use dotenv::dotenv;
use teloxide::prelude::*;
use tokio;

mod bot;
mod db;
mod web;

#[actix_rt::main]
async fn main() {
    dotenv();
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
