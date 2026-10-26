from worldcheck import gen, world


def tiny():
    nations = {n: {"alive": True, "allies": set(), "wars": set()} for n in ("France", "Spain", "Austria")}
    owners = {"Lorraine": "France", "Aragon": "Spain", "Bohemia": "Austria"}
    return world.World(1850, nations, owners, {"Louis": ("France", True), "Carlos": ("Spain", False)})


def test_capture_needs_war_and_the_right_owner():
    w = tiny()
    assert world.check_turn(w, ["France captures Aragon from Spain."])[0] == [("France captures Aragon from Spain.", "NOT_AT_WAR")]
    bad, _, w2 = world.check_turn(w, ["France declares war on Spain.", "France captures Aragon from Spain."])
    assert bad == [] and w2.owners["Aragon"] == "France"
    assert world.check_turn(w2, ["France captures Bohemia from Spain."])[0][0][1] == "WRONG_OWNER"


def test_dead_leader_ally_attack_and_anachronism():
    w = tiny()
    assert world.check_turn(w, ["Carlos of Spain addresses the council."])[0][0][1] == "DEAD_LEADER_ACTS"
    _, _, w2 = world.check_turn(w, ["France signs an alliance with Austria."])
    assert world.check_turn(w2, ["France declares war on Austria."])[0][0][1] == "ATTACKS_ALLY"
    assert world.check_turn(w, ["France deploys airplanes."])[0][0][1] == "ANACHRONISM"


def test_losing_the_last_province_eliminates_a_nation():
    w = tiny()
    _, _, w2 = world.check_turn(w, ["France declares war on Spain.", "France captures Aragon from Spain."])
    assert not w2.nations["Spain"]["alive"]
    assert world.check_turn(w2, ["Spain fields 40000 troops."])[0][0][1] == "ELIMINATED_NATION_ACTS"


def test_game_generator_is_reproducible():
    a, b = gen.make_game(3), gen.make_game(3)
    assert [x[1] for x in a] == [x[1] for x in b]
