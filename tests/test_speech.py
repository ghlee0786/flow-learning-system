from flow_learning_system.speech import native, norm, say_text, sino, speech_text, unreadable


def test_numbers():
    assert sino(2147483647) == "이십일억사천칠백사십팔만삼천육백사십칠"
    assert sino(10000) == "만"
    assert native(17) == "열일곱" and native(20) == "스무"
    assert norm("17개를 5개씩") == "열일곱 개를 다섯 개씩"
    assert norm("3번 칸") == "삼 번 칸"
    assert norm("-17 % 5") == "마이너스 십칠 % 오"
    assert norm("1.0.0.1") == "일 점 영 점 영 점 일"


def test_say_text():
    assert say_text("[[x += 3|엑스 플러스 이퀄 삼]]을 씁니다") == "엑스 플러스 이퀄 삼을 씁니다"
    assert say_text("`Console.WriteLine`은") == "콘솔 라이트라인은"
    assert say_text("i가 0") == "아이가 0"
    assert say_text("Foo는", {"Foo": "푸"}) == "푸는"


def test_unreadable():
    assert "ZzWord" in unreadable(speech_text("ZzWord를 씁니다"))
    assert unreadable(speech_text("리스트에 넣습니다")) == []
