import { strict as assert } from "assert";
import { buildDateFromEpoch } from "../tools/build_date";

describe("Reproducible build date", () => {
    it("uses the source timestamp when supplied", () => {
        assert.equal(buildDateFromEpoch("0"), "1970-01-01T00:00:00.000Z");
        assert.equal(
            buildDateFromEpoch("1700000000"),
            "2023-11-14T22:13:20.000Z",
        );
    });
    it("keeps the upstream clock default", () => {
        const before = Date.now();
        const actual = Date.parse(buildDateFromEpoch(undefined));
        assert.ok(actual >= before && actual <= Date.now());
    });
    it("rejects invalid timestamps", () => {
        for (const epoch of [
            "",
            "-1",
            "1.5",
            " 1",
            "NaN",
            "9007199254740992",
        ]) {
            assert.throws(() => buildDateFromEpoch(epoch));
        }
    });
});
