defmodule FixtureWorker.MixProject do
  use Mix.Project

  def project do
    [app: :fixture_worker, version: "0.1.0", elixir: "~> 1.16"]
  end

  def application do
    [extra_applications: [:logger], mod: {FixtureWorker.Application, []}]
  end
end
