import {
    LiveEventsProvider,
    useLiveRefresh,
} from "@/contexts/LiveEventsContext";
import { act, render } from "@testing-library/react";
const refreshUser = jest.fn();
jest.mock("@/contexts/AuthContext", () => ({
    useAuth: () => ({ refreshUser }),
}));
class Source {
    static instances: Source[] = [];
    listeners = new Map<string, (event: MessageEvent<string>) => void>();
    onerror: (() => void) | null = null;
    close = jest.fn();
    constructor(
        public url: string,
        public options: EventSourceInit,
    ) {
        Source.instances.push(this);
    }
    addEventListener(
        type: string,
        callback: (event: MessageEvent<string>) => void,
    ) {
        this.listeners.set(type, callback);
    }
    send(type: string, data: object = {}) {
        this.listeners.get(type)?.({
            data: JSON.stringify(data),
        } as MessageEvent<string>);
    }
}
function Consumer({ topic, refresh }: { topic: string; refresh: () => void }) {
    useLiveRefresh([topic], refresh);
    return null;
}
const originalSource = global.EventSource;
beforeEach(() => {
    jest.useFakeTimers();
    Source.instances = [];
    refreshUser.mockReset();
    global.EventSource = Source as unknown as typeof EventSource;
});
afterEach(() => {
    jest.useRealTimers();
    global.EventSource = originalSource;
});
async function advance(ms: number) {
    await act(async () => {
        jest.advanceTimersByTime(ms);
    });
}
test("shares one authenticated stream and refreshes matching screens after bursts", async () => {
    const monitoring = jest.fn();
    const notifications = jest.fn();
    const view = render(
        <LiveEventsProvider>
            <Consumer topic="monitoring" refresh={monitoring} />
            <Consumer topic="notifications" refresh={notifications} />
        </LiveEventsProvider>,
    );
    expect(Source.instances).toHaveLength(1);
    const source = Source.instances[0];
    expect(source.options.withCredentials).toBe(true);
    act(() => source.send("ready"));
    await advance(250);
    expect(monitoring).toHaveBeenCalledTimes(1);
    expect(notifications).toHaveBeenCalledTimes(1);
    act(() => {
        source.send("change", { topics: ["monitoring"] });
        source.send("change", { topics: ["monitoring"] });
    });
    await advance(250);
    expect(monitoring).toHaveBeenCalledTimes(2);
    expect(notifications).toHaveBeenCalledTimes(1);
    view.unmount();
    expect(source.close).toHaveBeenCalledTimes(1);
});
test("falls back when disconnected and catches up on reconnect", async () => {
    const refresh = jest.fn();
    render(
        <LiveEventsProvider>
            <Consumer topic="github" refresh={refresh} />
        </LiveEventsProvider>,
    );
    const source = Source.instances[0];
    await advance(30250);
    expect(refresh).toHaveBeenCalledTimes(1);
    act(() => source.send("ready"));
    await advance(250);
    expect(refresh).toHaveBeenCalledTimes(2);
    await advance(30250);
    expect(refresh).toHaveBeenCalledTimes(2);
    act(() => source.onerror?.());
    await advance(30250);
    expect(refresh).toHaveBeenCalledTimes(3);
    act(() => source.send("ready"));
    await advance(250);
    expect(refresh).toHaveBeenCalledTimes(4);
});
test("refreshes permissions silently and closes expired sessions", async () => {
    render(
        <LiveEventsProvider>
            <Consumer topic="github" refresh={jest.fn()} />
        </LiveEventsProvider>,
    );
    const source = Source.instances[0];
    act(() => source.send("change", { topics: ["access"] }));
    expect(refreshUser).toHaveBeenCalledWith(true);
    act(() => source.send("expired"));
    expect(source.close).toHaveBeenCalled();
});
test("uses current callbacks without opening another stream", async () => {
    const before = jest.fn();
    const after = jest.fn();
    const view = render(
        <LiveEventsProvider>
            <Consumer topic="monitoring" refresh={before} />
        </LiveEventsProvider>,
    );
    view.rerender(
        <LiveEventsProvider>
            <Consumer topic="monitoring" refresh={after} />
        </LiveEventsProvider>,
    );
    act(() => Source.instances[0].send("change", { topics: ["monitoring"] }));
    await advance(250);
    expect(before).not.toHaveBeenCalled();
    expect(after).toHaveBeenCalledTimes(1);
    expect(Source.instances).toHaveLength(1);
});
