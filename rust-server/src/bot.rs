use teloxide::{prelude::*, utils::command::BotCommand};

#[derive(BotCommand)]
#[command(rename="lowercase", description="these commands are available:")]
enum Command {
    #[command()]
    Add,
    #[command()]
    Help,
    #[command()]
    Start
}

async fn answer(cx :DispatcherHandlerCx<Message>, command: Command) -> ResponseResult<()> {
    let res = match command {
        Command::Start => cx.answer("not yet implemented"),
        Command::Help => cx.answer(Command::descriptions()),
        Command::Add => cx.answer("not yet implemented"),
    };

    res.send().await?;

    Ok(())
}

async fn handle_commands(rx: DispatcherHandlerRx<Message>) {
    rx.commands::<Command, &str>("mediaqbot")
        .for_each_concurrent(None, |(cx, command, _)| async move {
            answer(cx, command).await.log_on_error().await;
        })
        .await;
}

pub async fn run(bot: std::sync::Arc<Bot>) {
    Dispatcher::new(bot)
        .messages_handler(handle_commands)
        .dispatch()
        .await;
}
