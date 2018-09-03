#include "catch.hpp"

#include "donalonzo/hello_world.hpp"

TEST_CASE("hello_world") {
    SECTION("hello_world() returns \"Hello world\"") {
        REQUIRE(donalonzo::hello_world() == "Hello world");
    }
}