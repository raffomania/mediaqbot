use anyhow::Result;
use dotenv::dotenv;
use teloxide::prelude::*;
use tokio;

mod bot;
mod db;
mod web;

#[actix_rt::main]
async fn main() -> Result<()> {
    dotenv()?;
    run().await?;

    Ok(())
}

async fn run() -> Result<()> {
    teloxide::enable_logging!();

    let bot_instance = Bot::from_env();

    tokio::select! {
        r = bot::run(bot_instance) => r,
        r = web::run() => r
    }
}
