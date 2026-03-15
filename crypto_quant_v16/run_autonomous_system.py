def simulate_what_if(df_perf, scenario="bear"):
    df_sim = df_perf.copy()
    if scenario == "bear":
        df_sim["score"] *= 0.7
        df_sim["pnl"] *= -1.2
        df_sim["allocation"] *= 0.8
    elif scenario == "bull":
        df_sim["score"] *= 1.2
        df_sim["pnl"] *= 1.5
        df_sim["allocation"] *= 1.1
    return df_sim
import pandas as pd
import csv
import panel as pn
pn.extension()
import matplotlib.pyplot as plt
import psutil
import threading

# Historique pour affichage graphique
farm_history = {"Nursery": [], "Lab": [], "Robust": []}
cycle_times = []
def print_ray_status():
    try:
        summary = ray.nodes()
        print(f"[Ray] {len(summary)} nodes actifs")
        resources = ray.cluster_resources()
        print(f"[Ray] Ressources cluster : {resources}")
    except Exception as e:
        print(f"[Ray] Monitoring error: {e}")

def print_farm_stats(farm, name):
        # Stocke les stats pour affichage graphique
        if farm:
            scores = [s["score"] for s in farm]
            farm_history[name].append({
                "mean": sum(scores)/len(scores),
                "max": max(scores),
                "min": min(scores)
            })
    if not farm:
        print(f"[Farm {name}] Vide")
        return
    scores = [s["score"] for s in farm]
    print(f"[Farm {name}] Taille: {len(farm)}, Score moyen: {sum(scores)/len(scores):.4f}, Max: {max(scores):.4f}, Min: {min(scores):.4f}")
import ray
from quant_core.backtesting import BacktestingEngine

ray.init(ignore_reinit_error=True)


import time
import ray
from quant_core import data_engine, strategy_lab, backtesting, portfolio
from memecoin_alpha import launch_detector, sniper_engine, social_scanner, wallet_tracker, rug_detector
from supervision.bot_doctor import BotDoctor
from supervision.dashboard.panel import Dashboard

from self_improving.strategy_evolution_engine import StrategyEvolutionEngine
from self_improving.meta_strategy_ai import MetaStrategyAI
from self_improving.alpha_feedback_engine import AlphaFeedbackEngine
from self_improving.feature_feedback_engine import FeatureFeedbackEngine
from self_improving.regime_adaptation_engine import RegimeAdaptationEngine
from self_improving.knowledge_base import KnowledgeBase

# ---------------------------
# Config Notifications
# ---------------------------
TELEGRAM_TOKEN = "TON_BOT_TOKEN_ICI"
CHAT_ID = "TON_CHAT_ID_ICI"

# ---------------------------
# Modules à surveiller
# ---------------------------
modules = [
    data_engine,
    strategy_lab,
    backtesting,
    portfolio,
    launch_detector,
    sniper_engine,
    social_scanner,
    wallet_tracker,
    rug_detector
]

# ---------------------------
# Bot Doctor & Dashboard
# ---------------------------
bot_doctor = BotDoctor(modules, TELEGRAM_TOKEN, CHAT_ID)
dashboard = Dashboard(modules)

# ---------------------------
# Self-Improving AI
# ---------------------------
strategy_engine = StrategyEvolutionEngine()
meta_ai = MetaStrategyAI(strategy_engine)
alpha_feedback = AlphaFeedbackEngine()
feature_feedback = FeatureFeedbackEngine()
regime_adapt = RegimeAdaptationEngine()
knowledge_base = KnowledgeBase()

# Initialisation population et fermes
NUM_STRATEGIES = 10000
strategy_engine.generate_initial_population(NUM_STRATEGIES)

# Partition des fermes
nursery = strategy_engine.population[:NUM_STRATEGIES//4]    # nouvelles stratégies
lab = strategy_engine.population[NUM_STRATEGIES//4: NUM_STRATEGIES//2]  # en dev
robust = strategy_engine.population[NUM_STRATEGIES//2:]     # robustes / performantes

# ---------------------------
# Ray pour parallélisation
# ---------------------------
ray.init(ignore_reinit_error=True)

@ray.remote
def evaluate_strategy_remote(strategy):
    # Backtesting massif
    score = backtesting.evaluate_strategy(strategy)
    return {"name": strategy["name"], "score": score}

# ---------------------------
# Boucle principale autonome
# ---------------------------
def main_loop():
    step = 0
    memecoin_signals_history = []
    while True:
        start_cycle = time.time()
        step += 1
        print(f"\n=== Cycle autonome step {step} ===")

        # 1️⃣ Vérification de la santé des modules
        bot_doctor.run()

        # 2️⃣ Mise à jour du dashboard
        status = bot_doctor.monitor.check_all()
        for mod_name, mod_status in status.items():
            dashboard.update_status(mod_name, mod_status)
        dashboard.display()


        # 3️⃣ Exécution des modules classiques
        for module in modules:
            if module.is_healthy():
                module.run_step()

        # ---------------------------
        # 4️⃣ Memecoin Alpha
        # ---------------------------
        # 4a. Détection des nouveaux tokens
        new_tokens = launch_detector.detect_new_tokens()
        memecoin_opps = []
        for token in new_tokens:
            risk = rug_detector.evaluate(token)
            social_score = social_scanner.evaluate(token)
            wallet_score = wallet_tracker.evaluate(token)
            opportunity_score = (social_score + wallet_score) * (1 - risk)
            action = "HOLD"
            alert_msg = None
            if opportunity_score > 0.7:
                sniper_engine.buy(token)
                action = "BUY"
                alert_msg = f"[ALERTE] Sniper Engine: achat de {token['symbol']} avec score {opportunity_score:.2f}"
                print(alert_msg)
                # Exemple d'alerte Telegram (décommente si tu as la fonction)
                # send_telegram_alert(alert_msg)
            signal = {
                "symbol": token.get("symbol", "?"),
                "risk": risk,
                "social_score": social_score,
                "wallet_score": wallet_score,
                "opportunity_score": opportunity_score,
                "action": action,
                "cycle": step
            }
            memecoin_opps.append(signal)
            if alert_msg:
                memecoin_signals_history.append(signal)

        # Export CSV des signaux memecoin (toutes les 5 itérations)
        if step % 5 == 0 and memecoin_signals_history:
            df_signals = pd.DataFrame(memecoin_signals_history)
            df_signals.to_csv("memecoin_signals.csv", index=False)
            print("[Export] CSV des signaux memecoin mis à jour.")

        # Dashboard Panel/Matplotlib pour memecoin (toutes les 5 itérations)
        if step % 5 == 0 and memecoin_opps:
            df_memecoin = pd.DataFrame(memecoin_opps)
            memecoin_table = pn.widgets.Tabulator(df_memecoin, pagination='remote', page_size=20, sizing_mode='stretch_width')
            # Histogramme des scores d'opportunité
            fig, ax = plt.subplots(figsize=(7,3))
            df_memecoin['opportunity_score'].plot(kind='hist', bins=20, ax=ax, color='skyblue', edgecolor='black')
            ax.set_title('Distribution des scores d\'opportunité memecoin')
            ax.set_xlabel('Opportunity Score')
            ax.set_ylabel('Count')
            plt.tight_layout()
            # Scatter social vs wallet
            fig2, ax2 = plt.subplots(figsize=(7,3))
            ax2.scatter(df_memecoin['social_score'], df_memecoin['wallet_score'], c=df_memecoin['opportunity_score'], cmap='viridis', s=40)
            ax2.set_title('Social vs Whale Score (couleur: opportunity)')
            ax2.set_xlabel('Social Score')
            ax2.set_ylabel('Wallet Score')
            plt.tight_layout()
            memecoin_panel = pn.Column(
                pn.pane.Markdown(f"### Opportunités Memecoin détectées (cycle {step})"),
                memecoin_table,
                pn.pane.Matplotlib(fig, tight=True),
                pn.pane.Matplotlib(fig2, tight=True)
            )
            memecoin_panel.show()

        # Dashboard Panel enrichi pour memecoin avec graphiques
        if step % 5 == 0 and memecoin_opps:
            df_memecoin = pd.DataFrame(memecoin_opps)
            memecoin_table = pn.widgets.Tabulator(df_memecoin, pagination='remote', page_size=20, sizing_mode='stretch_width')

            # Graphique matplotlib : distribution des scores d'opportunité
            fig, ax = plt.subplots(figsize=(7,3))
            df_memecoin['opportunity_score'].plot(kind='hist', bins=20, ax=ax, color='skyblue', edgecolor='black')
            ax.set_title('Distribution des scores d\'opportunité memecoin')
            ax.set_xlabel('Opportunity Score')
            ax.set_ylabel('Count')
            plt.tight_layout()

            # Graphique matplotlib : scatter social_score vs wallet_score
            fig2, ax2 = plt.subplots(figsize=(7,3))
            ax2.scatter(df_memecoin['social_score'], df_memecoin['wallet_score'], c=df_memecoin['opportunity_score'], cmap='viridis', s=40)
            ax2.set_title('Social vs Whale Score (couleur: opportunity)')
            ax2.set_xlabel('Social Score')
            ax2.set_ylabel('Wallet Score')
            plt.tight_layout()

            memecoin_panel = pn.Column(
                pn.pane.Markdown(f"### Opportunités Memecoin détectées (cycle {step})"),
                memecoin_table,
                pn.pane.Matplotlib(fig, tight=True),
                pn.pane.Matplotlib(fig2, tight=True)
            )
            memecoin_panel.show()

        # 4️⃣ Backtesting massif des fermes
        for farm_name, farm in [("nursery", nursery), ("lab", lab), ("robust", robust)]:
            futures = [evaluate_strategy_remote.remote(s) for s in farm]
            results = ray.get(futures)
            for s, r in zip(farm, results):
                s["score"] = r["score"]

        # 5️⃣ Self-Improvement
        strategy_engine.evolve()
        top_strats = meta_ai.select_best_strategies(strategy_engine.population)
        combined_allocation = meta_ai.combine_strategies(top_strats)
        for s in top_strats:
            alpha_feedback.update(s)
            knowledge_base.store_strategy(s)

        # 6️⃣ Feature Feedback (simplifié)
        feature_feedback.evaluate_feature("momentum", 0.8)
        feature_feedback.evaluate_feature("volatility", 0.6)

        # 7️⃣ Adaptation selon le régime du marché
        market_data = data_engine.get_latest_market_data()
        regime = regime_adapt.detect_regime(market_data)
        print(f"Régime du marché détecté : {regime}")

        # 8️⃣ Allocation de portefeuille
        portfolio.allocate(top_strats)

        # 8b️⃣ Logging des performances dans la KnowledgeBase
        for s in top_strats:
            allocation = combined_allocation.get(s["name"], 0)
            # Simule un PnL (à adapter selon ta logique réelle)
            try:
                pnl = backtesting.simulate_pnl(s, allocation) if hasattr(backtesting, "simulate_pnl") else allocation * s["score"] * 0.01
            except Exception:
                pnl = 0
            knowledge_base.log_performance(s, s["score"], allocation, pnl)

        # 9️⃣ Affichage résumé fermes
        print(f"Top stratégies Nursery : {[s['name'] for s in sorted(nursery, key=lambda x: x['score'], reverse=True)[:5]]}")
        print(f"Top stratégies Lab : {[s['name'] for s in sorted(lab, key=lambda x: x['score'], reverse=True)[:5]]}")
        print(f"Top stratégies Robust : {[s['name'] for s in sorted(robust, key=lambda x: x['score'], reverse=True)[:5]]}")

        # 🔟 Monitoring Ray et fermes
        print_ray_status()
        print_farm_stats(nursery, "Nursery")
        print_farm_stats(lab, "Lab")
        print_farm_stats(robust, "Robust")

        # 🔟 Monitoring Ray et fermes
        print_ray_status()
        print_farm_stats(nursery, "Nursery")
        print_farm_stats(lab, "Lab")
        print_farm_stats(robust, "Robust")



        # 11️⃣ Affichage graphique, export CSV, dashboard web (toutes les 5 itérations)
        cycle_times.append(time.time() - start_cycle)
        if step % 5 == 0:
            # --- Matplotlib : scores fermes ---
            plt.figure(figsize=(10,5))
            for name in farm_history:
                if farm_history[name]:
                    means = [h["mean"] for h in farm_history[name]]
                    maxs = [h["max"] for h in farm_history[name]]
                    mins = [h["min"] for h in farm_history[name]]
                    plt.plot(means, label=f"{name} mean")
                    plt.plot(maxs, '--', label=f"{name} max")
                    plt.plot(mins, ':', label=f"{name} min")
            plt.title("Évolution des scores des fermes")
            plt.xlabel("Cycle")
            plt.ylabel("Score")
            plt.legend()
            plt.tight_layout()
            plt.show(block=False)
            plt.pause(0.1)
            plt.close()

            # --- Export CSV ---
            for name in farm_history:
                if farm_history[name]:
                    with open(f"farm_{name.lower()}_scores.csv", "w", newline="") as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=["mean", "max", "min"])
                        writer.writeheader()
                        writer.writerows(farm_history[name])
            print("[Export] CSV des scores des fermes mis à jour.")

            # --- Dashboard web interactif Panel : historique KnowledgeBase ---
            if hasattr(knowledge_base, "performance_history") and knowledge_base.performance_history:
                df_perf = pd.DataFrame(knowledge_base.performance_history)
                def plot_perf(df, title):
                    fig, ax = plt.subplots(figsize=(10,4))
                    df.groupby("timestamp")["score"].mean().plot(ax=ax, label="Score moyen")
                    df.groupby("timestamp")["pnl"].mean().plot(ax=ax, label="PnL moyen")
                    df.groupby("timestamp")["allocation"].mean().plot(ax=ax, label="Allocation moyenne")
                    ax.set_title(title)
                    ax.set_xlabel("Timestamp")
                    ax.set_ylabel("Valeur")
                    ax.legend()
                    plt.tight_layout()
                    return fig

                fig_perf = plot_perf(df_perf, "Historique des performances (Score, PnL, Allocation)")

                # Panel bouton pour simulation What-If
                def run_sim_bear(event=None):
                    df_sim = simulate_what_if(df_perf, scenario="bear")
                    fig_sim = plot_perf(df_sim, "Simulation Bear Market")
                    pn.pane.Matplotlib(fig_sim, tight=True).show()

                def run_sim_bull(event=None):
                    df_sim = simulate_what_if(df_perf, scenario="bull")
                    fig_sim = plot_perf(df_sim, "Simulation Bull Market")
                    pn.pane.Matplotlib(fig_sim, tight=True).show()

                btn_bear = pn.widgets.Button(name="Simuler Bear Market", button_type="danger")
                btn_bull = pn.widgets.Button(name="Simuler Bull Market", button_type="success")
                btn_bear.on_click(run_sim_bear)
                btn_bull.on_click(run_sim_bull)

                perf_panel = pn.Column(
                    pn.pane.Markdown(f"## Historique des performances (cycle {step})"),
                    pn.pane.Matplotlib(fig_perf, tight=True),
                    pn.Row(btn_bear, btn_bull)
                )
                perf_panel.show()

            # Affiche aussi le temps de cycle et l'utilisation CPU/mémoire
            print(f"Temps moyen d'un cycle : {sum(cycle_times)/len(cycle_times):.2f}s")
            print(f"CPU usage : {psutil.cpu_percent()}% | RAM : {psutil.virtual_memory().percent}%")

        # Pause pour cycle suivant
        time.sleep(5)  # ajuster selon fréquence souhaitée

if __name__ == "__main__":
    main_loop()
                bot_doctor = BotDoctor(modules, TELEGRAM_TOKEN, CHAT_ID)
                dashboard = Dashboard(modules)

                # ---------------------------
                # Self-Improving AI
                # ---------------------------
                strategy_engine = StrategyEvolutionEngine()
                meta_ai = MetaStrategyAI(strategy_engine)
                alpha_feedback = AlphaFeedbackEngine()
                feature_feedback = FeatureFeedbackEngine()
                regime_adapt = RegimeAdaptationEngine()
                knowledge_base = KnowledgeBase()

                # Initialisation population
                strategy_engine.generate_initial_population(100)

                # ---------------------------
                # Boucle principale autonome
                # ---------------------------
                def main_loop():
                    step = 0
                    while True:
                        step += 1
                        print(f"\n=== Cycle autonome step {step} ===")

                        # 1️⃣ Vérification de la santé des modules
                        bot_doctor.run()

                        # 2️⃣ Mise à jour du dashboard
                        status = bot_doctor.monitor.check_all()
                        for mod_name, mod_status in status.items():
                            dashboard.update_status(mod_name, mod_status)
                        dashboard.display()

                        # 3️⃣ Exécution des modules
                        for module in modules:
                            if module.is_healthy():
                                module.run_step()


                        # 4️⃣ Backtesting massif en parallèle avec Ray
                        futures = [evaluate_strategy_remote.remote(s) for s in strategy_engine.population]
                        results = ray.get(futures)
                        for s, r in zip(strategy_engine.population, results):
                            s["score"] = r["score"]

                        # 5️⃣ Self-Improvement
                        strategy_engine.evolve()
                        top_strats = meta_ai.select_best_strategies(strategy_engine.population)
                        combined_allocation = meta_ai.combine_strategies(top_strats)
                        for s in top_strats:
                            alpha_feedback.update(s)
                            knowledge_base.store_strategy(s)

                        # 6️⃣ Feature Feedback (simplifié)
                        # Ici tu peux lier avec feature_engine pour calculer score features
                        # Exemple : random
                        feature_feedback.evaluate_feature("momentum", 0.8)
                        feature_feedback.evaluate_feature("volatility", 0.6)

                        # 7️⃣ Adaptation selon le régime du marché
                        market_data = data_engine.get_latest_market_data()
                        regime = regime_adapt.detect_regime(market_data)
                        print(f"Régime du marché détecté : {regime}")

                        # 8️⃣ Allocation de portefeuille
                        portfolio.allocate(top_strats)

                        # Pause pour cycle suivant
                        time.sleep(5)  # à ajuster selon la fréquence souhaitée

                if __name__ == "__main__":
                    main_loop()
