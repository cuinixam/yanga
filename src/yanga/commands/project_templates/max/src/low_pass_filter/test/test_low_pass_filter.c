#include "gtest/gtest.h"
#include "low_pass_filter.h"

// Test a sequence of values through the low pass filter
TEST(LowPassFilterTest, Sequence) {
    double input[] = {1.0, 2.0, 3.0, 4.0, 5.0};
    double expected[] = {0.1, 0.29, 0.561, 0.9049, 1.31441};

    double filtered_value = 0.0;
    for (int i = 0; i < 5; i++) {
        filtered_value = low_pass_filter(filtered_value, input[i]);
        EXPECT_NEAR(filtered_value, expected[i], 0.001);
    }
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
