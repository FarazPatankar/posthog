import { PageHeader } from 'lib/components/PageHeader'
import React, { useEffect, useState } from 'react'
import { PostHogLessons } from './modules/posthogLessons'
import { TiledIconModule, TileParams } from './modules/tiledIconModule'

import { DiscoverInsightsModule } from './modules/discoverInsight'
import { Button, Layout, Space, Tooltip } from 'antd'
import { SlackOutlined, UserAddOutlined, RocketOutlined, GithubOutlined } from '@ant-design/icons'

import './Home.scss'

const { Content } = Layout
import { useActions, useValues } from 'kea'

import { teamLogic } from 'scenes/teamLogic'
import { CreateInviteModalWithButton } from 'scenes/organization/Settings/CreateInviteModal'
import { preflightLogic } from 'scenes/PreflightCheck/logic'
import { navigationLogic } from '~/layout/navigation/navigationLogic'
import { userLogic } from 'scenes/userLogic'
import { eventUsageLogic } from 'lib/utils/eventUsageLogic'

function HeaderCTAs(): JSX.Element {
    const { setInviteMembersModalOpen } = useActions(navigationLogic)
    const { inviteMembersModalOpen } = useValues(navigationLogic)
    const { preflight } = useValues(preflightLogic)
    const [showToolTip, setShowToolTip] = useState(false)

    return (
        <Space direction={'vertical'}>
            <div>
                <Tooltip
                    placement="bottom"
                    visible={showToolTip && !inviteMembersModalOpen}
                    title={"Because insights are better when they're shared with friends."}
                >
                    <div>
                        {preflight?.email_service_available ? (
                            <Button
                                onMouseLeave={() => {
                                    setShowToolTip(false)
                                }}
                                onMouseEnter={() => {
                                    {
                                        setShowToolTip(true)
                                    }
                                }}
                                type="primary"
                                icon={<UserAddOutlined />}
                                onClick={() => {
                                    setInviteMembersModalOpen(true)
                                }}
                                data-attr="project-home-invite-team-members"
                                style={{ width: '100%' }}
                            >
                                Invite Team Members
                            </Button>
                        ) : (
                            <CreateInviteModalWithButton
                                onMouseLeave={() => {
                                    setShowToolTip(false)
                                }}
                                onMouseEnter={() => {
                                    {
                                        setShowToolTip(true)
                                    }
                                }}
                                block
                            />
                        )}
                    </div>
                </Tooltip>
            </div>
        </Space>
    )
}

export function Home(): JSX.Element {
    const { currentTeam } = useValues(teamLogic)
    const { user } = useValues(userLogic)
    const { reportProjectHomeSeen } = useActions(eventUsageLogic)

    const communitySources: TileParams[] = [
        {
            icon: <SlackOutlined />,
            title: 'Hang out in Slack',
            targetPath: 'https://posthog.com/slack?s=app&utm_content=project-home',
            openInNewTab: true,
            hoverText:
                'Talk with other PostHog users, get support on issues, and exclusive access to features in beta development.',
        },
        {
            icon: <GithubOutlined />,
            title: 'Check out our code',
            openInNewTab: true,
            targetPath: 'https://github.com/PostHog/posthog',
            hoverText: 'Submit a pull request and snag some PostHog merch!',
        },
    ]

    const communityModule = (
        <TiledIconModule
            tiles={communitySources}
            analyticsModuleKey="community"
            header="Join the PostHog Community"
            subHeader="Share your learnings with other PostHog users. Learn about the latest in product analytics directly from the PostHog team and members in our community."
        />
    )

    const installationSources: TileParams[] = [
        {
            icon: <RocketOutlined />,
            title: 'Install PostHog',
            targetPath: '/ingestion',
            hoverText:
                'Our broad library support and simple API make it easy to install PostHog anywhere in your stack.',
            class: 'thumbnail-tile-install',
        },
    ]
    const installModule = (
        <TiledIconModule
            tiles={installationSources}
            analyticsModuleKey="install"
            header="Install PostHog"
            subHeader="Installation is easy. Choose from one of our libraries or our simple API."
        />
    )

    const layoutTeamHasEvents = (
        <>
            <DiscoverInsightsModule />
            <PostHogLessons />
            {communityModule}
        </>
    )

    const layoutTeamNeedsEvents = (
        <>
            {installModule}
            {communityModule}
            <PostHogLessons />
        </>
    )
    const teamHasData = user?.team?.ingested_event

    useEffect(() => {
        reportProjectHomeSeen(teamHasData || false)
    }, [])

    return (
        <Layout>
            <div style={{ marginBottom: 128 }} className={'home-container'}>
                <Space direction="vertical">
                    <PageHeader
                        title={`${currentTeam?.name ?? ''} Home`}
                        caption={
                            teamHasData ? undefined : 'Welcome to PostHog! Install one of our libraries to get started.'
                        }
                        buttons={<HeaderCTAs />}
                    />
                    <Content>
                        <Space direction="vertical">{teamHasData ? layoutTeamHasEvents : layoutTeamNeedsEvents}</Space>
                    </Content>
                </Space>
            </div>
        </Layout>
    )
}
