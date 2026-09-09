export function buildDateFromEpoch(epoch: string | undefined): string {
    if (epoch === undefined) {
        return new Date().toISOString();
    }
    if (!/^\d+$/.test(epoch)) {
        throw new Error("Invalid SOURCE_DATE_EPOCH");
    }
    const seconds = Number(epoch);
    if (!Number.isSafeInteger(seconds)) {
        throw new Error("Invalid SOURCE_DATE_EPOCH");
    }
    return new Date(seconds * 1000).toISOString();
}
