defmodule FixtureWorker.Worker do
  use GenServer

  def start_link(_options) do
    GenServer.start_link(__MODULE__, %{processed: 0}, name: __MODULE__)
  end

  @impl true
  def init(state) do
    Process.send_after(self(), :poll, 10)
    {:ok, state}
  end

  @impl true
  def handle_info(:poll, state) do
    next_state = Map.update!(state, :processed, &(&1 + 1))
    {:noreply, next_state}
  end
end
