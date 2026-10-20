"""Visualizações estáticas com unidades e origem explícitas."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def render(analysis, directory):
    label = 'Dados fictícios; calendário não representa NASDAQ' if analysis.dataset.metadata['synthetic'] else 'Dados fornecidos; calendário declarado'
    with plt.rc_context({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False}):
        fig, axes = plt.subplots(2, 2, figsize=(13, 8), layout='constrained')
        for symbol, frame in analysis.daily.groupby('symbol'):
            dates = pd.to_datetime(frame.date)
            axes[0, 0].plot(dates, frame.base_100, label=symbol, linewidth=1.2)
            axes[0, 1].plot(dates, frame.volatility_20_annualized * 100, label=symbol, linewidth=.9)
            axes[1, 0].plot(dates, frame.drawdown * 100, label=symbol, linewidth=1)
        axes[0, 0].set(title='Preço ajustado normalizado', ylabel='Base 100 no início da janela')
        axes[0, 0].legend(ncol=2)
        axes[0, 1].set(title='Volatilidade histórica: 20 retornos', ylabel='% anualizado (convenção 252)')
        axes[1, 0].set(title='Drawdown desde o início da janela', ylabel='% abaixo do máximo acumulado')
        monthly_volume = analysis.monthly.groupby('month').volume.sum()
        axes[1, 1].bar(monthly_volume.index, monthly_volume / 1e6, color='#247c94')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].set(title='Volume agregado dos ativos', ylabel='Milhões de ações (bruto)')
        for ax in (axes[0, 0], axes[0, 1], axes[1, 0]):
            ax.tick_params(axis='x', rotation=20)
        fig.suptitle(f'Análise temporal descritiva | {label}', fontsize=13)
        fig.savefig(directory / 'painel.png', dpi=140)
        plt.close(fig)
        matrix = analysis.monthly.pivot(index='symbol', columns='month', values='return_monthly_price') * 100
        fig, ax = plt.subplots(figsize=(12, 4), layout='constrained')
        finite = matrix.to_numpy()[np.isfinite(matrix.to_numpy())]
        scale = max(float(np.abs(finite).max()), 1) if finite.size else 1
        image = ax.imshow(matrix.to_numpy(), cmap='RdYlGn', vmin=-scale, vmax=scale, aspect='auto')
        ax.set_xticks(range(len(matrix.columns)), matrix.columns, rotation=45, ha='right')
        ax.set_yticks(range(len(matrix.index)), matrix.index)
        for y in range(len(matrix)):
            for x in range(len(matrix.columns)):
                value = matrix.iloc[y, x]
                ax.text(x, y, '—' if pd.isna(value) else f'{value:.1f}', ha='center', va='center', fontsize=8)
        fig.colorbar(image, ax=ax, label='Retorno de preço (%)')
        ax.set_title('Retorno mensal de preço ajustado | ' + label)
        fig.savefig(directory / 'retornos_mensais.png', dpi=140)
        plt.close(fig)
