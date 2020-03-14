use anyhow::{anyhow, Context, Result};
use bincode;
use sled;
use teloxide::{prelude::*, utils::command::BotCommand};
use uuid::Uuid;

use crate::db;

#[derive(BotCommand)]
#[command(rename = "lowercase", description = "these commands are available:")]
enum Command {
    #[command(description = "Add a video")]
    Add,
    #[command()]
    Help,
    #[command()]
    Start,
}

async fn add(cx: DispatcherHandlerCx<Message>) -> Result<()> {
    let text = if let Some(text) = cx.update.text() {
        text
    } else {
        cx.answer("please send me a video URL").send().await?;
        return Ok(());
    };
    let parts: Vec<&str> = text.split_whitespace().collect();
    if parts.len() > 2 {
        cx.answer("please send only one url").send().await?;
        return Ok(());
    } else if parts.len() < 2 {
        cx.answer("please send a video url").send().await?;
        return Ok(());
    }

    let url = parts[1];

    let tree = sled::open("db.sled")?;
    let chat_name = db::get_or_create_chat_name(cx.chat_id(), &tree)?;
    let uuid = Uuid::new_v4();
    let mut queue = db::get_or_create_queue(&tree, &chat_name)?;
    queue.push((uuid, url.into()));

    println!("{:?}", queue);

    tree.insert(&chat_name, bincode::serialize(&queue)?)?;

    Ok(())
}

async fn help(cx: DispatcherHandlerCx<Message>) -> Result<()> {
    cx.answer(Command::descriptions()).send().await?;
    Ok(())
}

async fn start(cx: DispatcherHandlerCx<Message>) -> Result<()> {
    let tree = sled::open("db.sled")?;
    let chat_name = db::get_or_create_chat_name(cx.chat_id(), &tree)?;
    cx.answer(format!(
        "Your chat ID is \"{}\". Use this when starting the mediaqbot client.",
        chat_name
    ))
    .send()
    .await?;
    Ok(())
}

async fn answer(cx: DispatcherHandlerCx<Message>, command: Command) -> Result<()> {
    match command {
        Command::Add => add(cx).await?,
        Command::Help => help(cx).await?,
        Command::Start => start(cx).await?,
    };

    Ok(())
}

async fn handle_commands(rx: DispatcherHandlerRx<Message>) {
    rx.commands::<Command, &str>("mediaqbot")
        .for_each_concurrent(None, |(cx, command, _)| async move {
            answer(cx, command).await.log_on_error().await;
        })
        .await;
}

pub async fn run(bot: std::sync::Arc<Bot>) -> Result<()> {
    Dispatcher::new(bot)
        .messages_handler(handle_commands)
        .dispatch()
        .await;

    Ok(())
}
