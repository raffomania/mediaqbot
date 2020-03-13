use teloxide::prelude::*;
use dotenv::dotenv;

mod bot;

#[tokio::main]
async fn main() {
    dotenv().expect("please create an .env file");
    run().await;
}

async fn run() {
    teloxide::enable_logging!();

    let bot_instance = Bot::from_env();

    bot::run(bot_instance).await;
}
