import { useState } from 'react';
import { useWatchlist } from '../hooks/useWatchlist';

export default function Watchlist() {
    const { watchlist, addStock, removeStock, updateNote } = useWatchlist();
    const [newTicker, setNewTicker] = useState('');
    const [newName, setNewName] = useState('');

    const handleAdd = (e: React.FormEvent) => {
        e.preventDefault();
        if (newTicker && newName) {
            addStock(newTicker, newName);
            setNewTicker('');
            setNewName('');
        }
    };

    return (
        <div className="flex flex-col gap-8 max-w-5xl mx-auto">
            <h1 className="text-2xl font-bold text-white">관심종목 (Watchlist)</h1>

            {/* Add Form */}
            <div className="bg-card-dark border border-border-dark rounded-xl p-6">
                <h2 className="text-lg font-bold text-white mb-4">새 종목 추가</h2>
                <form onSubmit={handleAdd} className="flex flex-col md:flex-row gap-4 items-end">
                    <div className="flex flex-col gap-2 flex-1 w-full">
                        <label className="text-xs font-bold text-text-subtle">종목코드 (Ticker)</label>
                        <input
                            type="text"
                            value={newTicker}
                            onChange={(e) => setNewTicker(e.target.value)}
                            placeholder="예: 005930"
                            className="bg-background-dark border border-border-dark rounded-lg px-4 py-2 text-white outline-none focus:border-primary w-full"
                        />
                    </div>
                    <div className="flex flex-col gap-2 flex-[2] w-full">
                        <label className="text-xs font-bold text-text-subtle">종목명 (Name)</label>
                        <input
                            type="text"
                            value={newName}
                            onChange={(e) => setNewName(e.target.value)}
                            placeholder="예: 삼성전자"
                            className="bg-background-dark border border-border-dark rounded-lg px-4 py-2 text-white outline-none focus:border-primary w-full"
                        />
                    </div>
                    <button
                        type="submit"
                        className="bg-primary hover:bg-blue-600 text-white font-bold px-6 py-2 rounded-lg transition-colors whitespace-nowrap h-[42px] w-full md:w-auto"
                    >
                        추가
                    </button>
                </form>
            </div>

            {/* List */}
            <div className="bg-card-dark border border-border-dark rounded-xl overflow-hidden">
                {watchlist.length === 0 ? (
                    <div className="p-10 text-center text-text-subtle">
                        등록된 관심종목이 없습니다.
                        <button
                            onClick={() => addStock('005930', '삼성전자')}
                            className="block mx-auto mt-4 text-primary hover:underline"
                        >
                            삼성전자 예시 추가
                        </button>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="bg-[#151e1d] border-b border-border-dark text-text-subtle">
                                    <th className="px-6 py-4 text-left font-bold w-24">Ticker</th>
                                    <th className="px-6 py-4 text-left font-bold w-40">Name</th>
                                    <th className="px-6 py-4 text-left font-bold">Memo</th>
                                    <th className="px-6 py-4 text-right font-bold w-32">Added</th>
                                    <th className="px-6 py-4 text-right font-bold w-24">Action</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-dark/50">
                                {watchlist.map((item) => (
                                    <tr key={item.ticker} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4 text-text-subtle font-mono">{item.ticker}</td>
                                        <td className="px-6 py-4 text-white font-bold">{item.name}</td>
                                        <td className="px-6 py-4">
                                            <input
                                                type="text"
                                                value={item.note}
                                                onChange={(e) => updateNote(item.ticker, e.target.value)}
                                                placeholder="메모를 입력하세요..."
                                                className="bg-transparent border-b border-transparent focus:border-primary outline-none text-gray-300 w-full placeholder:text-gray-600"
                                            />
                                        </td>
                                        <td className="px-6 py-4 text-right text-text-subtle text-xs">{item.addedAt}</td>
                                        <td className="px-6 py-4 text-right">
                                            <button
                                                onClick={() => removeStock(item.ticker)}
                                                className="text-red-500 hover:text-red-400 p-1 hover:bg-red-500/10 rounded transition-colors"
                                            >
                                                <span className="material-symbols-outlined text-[20px]">delete</span>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
