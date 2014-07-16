import const
import fight
import handler_game
import merc
import state_checks


def spell_word_of_recall(sn, level, ch, victim, target):
    # RT recall spell is back */
    if victim.is_npc():
        return

    if merc.ROOM_VNUM_TEMPLE not in merc.roomTemplate:
        victim.send("You are completely lost.\n")
        return
    location = merc.roomTemplate[merc.ROOM_VNUM_TEMPLE]

    if state_checks.IS_SET(victim.in_room.room_flags, merc.ROOM_NO_RECALL) or victim.is_affected(merc.AFF_CURSE):
        victim.send("Spell failed.\n")
        return

    if victim.fighting:
        fight.stop_fighting(victim, True)

    ch.move //= 2
    handler_game.act("$n disappears.", victim, None, None, merc.TO_ROOM)
    victim.from_environment()
    victim.to_environment(location)
    handler_game.act("$n appears in the room.", victim, None, None, merc.TO_ROOM)
    victim.do_look("auto")


const.register_spell(const.skill_type("word of recall",
                          {'mage': 32, 'cleric': 28, 'thief': 40, 'warrior': 30},
                          {'mage': 1, 'cleric': 1, 'thief': 2, 'warrior': 2},
                          spell_word_of_recall, merc.TAR_CHAR_SELF, merc.POS_RESTING, None,
                          const.SLOT(42), 5, 12, "", "!Word of Recall!", ""))  # * Dragon breath */)
