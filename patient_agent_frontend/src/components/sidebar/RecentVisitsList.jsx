import React from 'react'

export default function RecentVisitsList({ visits }) {
  if (!visits || visits.length === 0) {
    return <div className="recent-visits-empty">暂无近期就诊记录</div>
  }

  return (
    <div className="recent-visits-list">
      {visits.slice(0, 3).map((visit) => (
        <div key={visit.visitId} className="recent-visit-summary">
          <div className="recent-visit-summary-date">{visit.visitDate || '--'}</div>
          <div className="recent-visit-summary-body">
            <span className="recent-visit-summary-dept">{visit.department || '--'}</span>
            <span className="recent-visit-summary-divider" aria-hidden="true" />
            <span className="recent-visit-summary-doctor">{visit.doctorName || '--'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
