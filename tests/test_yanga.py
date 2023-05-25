from yanga.yanga import Yanga, main


def test_yanga():
    yanga = Yanga()
    assert yanga
    print("Call main")
    main()
