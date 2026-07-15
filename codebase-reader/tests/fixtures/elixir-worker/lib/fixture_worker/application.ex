defmodule FixtureWorker.Application do
  use Application

  @impl true
  def start(_type, _args) do
    children = [{FixtureWorker.Worker, []}]
    Supervisor.start_link(children, strategy: :one_for_one, name: FixtureWorker.Supervisor)
  end
end
