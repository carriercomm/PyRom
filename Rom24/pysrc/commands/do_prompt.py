import merc
import interp


def do_prompt(ch, argument):
    if not argument:
        if merc.IS_SET(ch.comm, merc.COMM_PROMPT):
            ch.send("You will no longer see prompts.\n")
            ch.comm = merc.REMOVE_BIT(ch.comm, merc.COMM_PROMPT)
        else:
            ch.send("You will now see prompts.\n")
            ch.comm = merc.SET_BIT(ch.comm, merc.COMM_PROMPT)
        return
    if argument.lower() == "all":
        buf = "<%hhp %mm %vmv> "
    else:
        if len(argument) > 50:
            argument = argument[:50]
        buf = argument
        if buf.endswith("%c"):
            buf += " "
    ch.prompt = buf
    ch.send("Prompt set to %s\n" % ch.prompt)
    return

interp.cmd_table['prompt'] = interp.cmd_type('prompt', do_prompt, merc.POS_DEAD, 0, merc.LOG_NORMAL, 1)