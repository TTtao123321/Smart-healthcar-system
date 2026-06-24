import { useEffect, useState } from 'react'
import PatientProfileCard from './PatientProfileCard.jsx'
import HospitalScheduleCard from './HospitalScheduleCard.jsx'
import { patientApi } from '../../api/index.js'
import { patientProfile } from '../../mocks/patientProfile.js'
import { scheduleDateLabel, scheduleDepartments } from '../../mocks/scheduleData.js'

const fallbackSidebar = {
  profile: patientProfile,
  recentVisits: patientProfile.recentVisits,
  schedule: {
    dateLabel: scheduleDateLabel,
    departments: scheduleDepartments,
  },
}

export default function PatientSidebar({ user, onSendChat }) {
  const [sidebar, setSidebar] = useState(fallbackSidebar)
  const [loading, setLoading] = useState(true)
  const [loadFailed, setLoadFailed] = useState(false)

  useEffect(() => {
    let active = true

    patientApi.getSidebar()
      .then((res) => {
        if (!active) return
        setSidebar(res.data)
        setLoadFailed(false)
      })
      .catch(() => {
        if (!active) return
        setLoadFailed(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  return (
    <aside className="patient-sidebar">
      <PatientProfileCard
        profile={{ ...sidebar.profile, recentVisits: sidebar.recentVisits }}
        loading={loading}
        loadFailed={loadFailed}
      />
      <HospitalScheduleCard
        user={user}
        onSendChat={onSendChat}
        departments={sidebar.schedule?.departments || []}
        dateLabel={sidebar.schedule?.dateLabel || scheduleDateLabel}
        loading={loading}
      />
    </aside>
  )
}
