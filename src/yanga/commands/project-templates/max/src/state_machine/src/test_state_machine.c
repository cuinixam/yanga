#include "gtest/gtest.h"
#include "state_machine.h"

TEST(StateMachineTest, Transitions) {
    // Test transition from STATE_A to STATE_B
    EXPECT_EQ(next_state(STATE_A), STATE_B);

    // Test transition from STATE_B to STATE_C
    EXPECT_EQ(next_state(STATE_B), STATE_C);

    // Test transition from STATE_C to STATE_A
    EXPECT_EQ(next_state(STATE_C), STATE_A);
}

TEST(StateMachineTest, DefaultTransition) {
    // Test default case
    EXPECT_EQ(next_state((State)9999), STATE_A);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
